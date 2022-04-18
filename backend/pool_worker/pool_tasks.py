# -*- coding: utf-8 -*-
import asyncio
import traceback
from abc import ABC, abstractmethod

from aiohttp import client_exceptions

from common.languages import _local_
from common.log.journal import system_logger
from common.models.auth import Entity
from common.models.authentication_directory import AuthenticationDirectory
from common.models.pool import AutomatedPool, Pool
from common.models.task import PoolTaskType, Task, TaskStatus
from common.models.vm import Vm
from common.utils import cancel_async_task
from common.veil.veil_errors import PoolCreationError, VmCreationError
from common.veil.veil_gino import EntityType, Status
from common.veil.veil_redis import redis_get_lock, redis_release_lock_no_errors


# Добавление задачи:
# 1) В файле common/models/task.py в конец enum PoolTaskType добавить новое имя (MY_TASK например)
# 2) В файле pool_worker/poll_tasks.py наследовать от AbstractTask и в методе do_task реализуем задачу MyTask.

# Локи:
# Лок пула используется для обеспечения работы над пулом только одной задачи единовременно.
# Лок шаблона диктуется ограничением контролера (Единовременно из шаблона может создаваться только одна вм
# и следовательно только один пул)
# Обязательно соблюдать один и тот же порядок лока, иначе дед лок.


class AbstractTask(ABC):
    """Выполняет задачу do_task."""

    task_list = (
        list()
    )  # Список, в котором держим объекты выполняемым в данный момент таскок
    task_type = None

    def __init__(self):

        self.task_model = None
        self._coroutine = None
        self._task_priority = 1
        self._associated_entity_name = ""

    @staticmethod
    def get_task_list_shallow_copy():
        return list(AbstractTask.task_list)

    async def cancel(self, resumable=False, wait_for_result=True):
        """Отменить таску."""
        if self.task_model:
            await self.task_model.update(resumable=resumable).apply()

        if self._coroutine:
            await system_logger.debug(
                "cancel self.coroutine {}".format(self._coroutine)
            )
            await cancel_async_task(self._coroutine, wait_for_result)
            self._coroutine = None

    @abstractmethod
    async def get_user_friendly_text(self):
        return ""

    @abstractmethod
    async def do_task(self):
        """Корутина, в которой будет выполняться таска."""
        raise NotImplementedError

    async def do_on_cancel(self):
        """Действия при отмене корутины do_task."""
        pass

    async def do_on_fail(self):
        """Действия при фэйле корутины do_task."""
        pass

    async def execute(self, task_id):
        """Выполнить корутину do_task."""
        self.task_model = await Task.get(task_id)

        if not self.task_model:
            await system_logger.error(
                "AbstractTask.execute: logical error. No such task {}.".format(task_id)
            )
            return

        await self.task_model.update(priority=self._task_priority).apply()
        user_friendly_text = await self.get_user_friendly_text()

        try:
            # Добавить себя в список выполняющихся задач
            AbstractTask.task_list.append(self)

            # set task status
            await self.task_model.set_status(TaskStatus.IN_PROGRESS, user_friendly_text)

            await system_logger.info(_local_("Task '{}' started.").format(user_friendly_text),
                                     user=self.task_model.creator)

            await self.do_task()
            await self.task_model.set_status(TaskStatus.FINISHED, user_friendly_text)
            await system_logger.info(_local_("Task '{}' finished successfully.").format(user_friendly_text),
                                     user=self.task_model.creator)

        except asyncio.CancelledError:
            await self.task_model.set_status(TaskStatus.CANCELLED, user_friendly_text)
            await system_logger.warning(_local_("Task '{}' cancelled.").format(user_friendly_text))

            await self.do_on_cancel()

        except Exception as ex:
            message = _local_("Task '{}' failed.").format(user_friendly_text)

            await self.task_model.set_status(TaskStatus.FAILED, message + " " + str(ex))

            description = str(ex)
            # asyncio.TimeoutError и PoolCreationError считаются ожидаемым исключением, поэтому traceback не требуется
            if not isinstance(ex, asyncio.TimeoutError) and not isinstance(ex, PoolCreationError):
                tb = traceback.format_exc()
                description += (" " + tb)
            await system_logger.warning(message=message,
                                        description=description,
                                        user=self.task_model.creator)
            await self.do_on_fail()

        finally:
            # Удалить себя из списка выполняющихся задач
            AbstractTask.task_list.remove(self)

    def execute_in_async_task(self, task_id):
        """Запустить корутину асинхронно."""
        self._coroutine = asyncio.get_event_loop().create_task(self.execute(task_id))

    def _get_related_progressing_tasks(self):
        """Получить выполняющиеся таски связанные с сущностью исключая текущую таску."""
        tasks_related_to_cur_pool = list()

        for task in AbstractTask.task_list:
            task_entity_cond = task.task_model.entity_id == self.task_model.entity_id
            task_obj_cond = task.task_model.id != self.task_model.id
            if task_entity_cond and task_obj_cond:
                tasks_related_to_cur_pool.append(task)
        return tasks_related_to_cur_pool

    async def _get_associated_entity_name(self):
        # Запоминаем имя так как его не будет после удаления пула, например.
        if self._associated_entity_name == "" and self.task_model:
            # В зависимости от типа сущности узнаем verbose_name
            # get entity_type
            entity = await Entity.query.where(
                Entity.entity_uuid == self.task_model.entity_id
            ).gino.first()
            if entity:
                if entity.entity_type == EntityType.POOL:
                    from common.models.pool import Pool

                    pool = await Pool.get(self.task_model.entity_id)
                    self._associated_entity_name = pool.verbose_name if pool else ""

                elif entity.entity_type == EntityType.VM:
                    from common.models.vm import Vm

                    vm = await Vm.get(self.task_model.entity_id)
                    self._associated_entity_name = vm.verbose_name if vm else ""

        return self._associated_entity_name


class InitPoolTask(AbstractTask):

    task_type = PoolTaskType.POOL_CREATE

    def __init__(self):
        super().__init__()

        self._task_priority = 2

    async def get_user_friendly_text(self):
        entity_name = await self._get_associated_entity_name()
        return _local_("Creation of pool {}.").format(entity_name)

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError("InitPoolTask: AutomatedPool doesnt exist")

        async with redis_get_lock(str(automated_pool.id)):
            async with redis_get_lock(str(automated_pool.template_id)):
                # Добавляем машины
                try:
                    pool = await Pool.get(self.task_model.entity_id)
                    await pool.update(status=Status.CREATING).apply()

                    await automated_pool.add_initial_vms(self.task_model.creator)
                except PoolCreationError:
                    await automated_pool.deactivate()
                    # Чтобы проблема была передана внешнему обработчику в AbstractTask
                    raise
                except asyncio.CancelledError:
                    await system_logger.warning(_local_("Pool Creation cancelled."))
                    await automated_pool.deactivate()
                    raise
                except Exception as E:
                    await system_logger.error(
                        message=_local_("Failed to init pool."), description=str(E)
                    )
                    await automated_pool.deactivate()
                    raise E

            # Подготавливаем машины. Находимся на этом отступе так как нам нужен лок пула но не нужен лок шаблона
            try:
                if automated_pool.preparation_required():
                    results_future = await automated_pool.prepare_initial_vms(self.task_model.creator)
                    # Если есть отмененные корутины, то считаем, что инициализация пула отменена
                    for response in results_future:
                        if isinstance(response, asyncio.CancelledError):
                            raise asyncio.CancelledError

            except asyncio.CancelledError:
                await automated_pool.deactivate()
                raise
            except Exception as E:
                await automated_pool.deactivate()
                await system_logger.error(
                    message=_local_("Pool initialization VM(s) preparation error."),
                    description=str(E),
                )
                raise E

        # Активируем пул
        await automated_pool.activate()


class ExpandPoolTask(AbstractTask):

    task_type = PoolTaskType.POOL_EXPAND

    def __init__(self, ignore_reserve_size=False):
        super().__init__()

        self.ignore_reserve_size = (
            ignore_reserve_size
        )  # расширение не смотря на достаточный резерв

    async def get_user_friendly_text(self):
        entity_name = await self._get_associated_entity_name()
        return _local_("Expanding of pool {}.").format(entity_name)

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError("ExpandPoolTask: AutomatedPool doesnt exist")

        vm_list = list()

        async with redis_get_lock(str(automated_pool.id)):
            async with redis_get_lock(str(automated_pool.template_id)):
                # Check that total_size is not reached
                pool = await Pool.get(automated_pool.id)
                vm_amount_in_pool = await pool.get_vm_amount()

                # If reached then do nothing
                if vm_amount_in_pool >= automated_pool.total_size:
                    return

                # Если подогретых машин слишком мало, то пробуем добавить еще
                # self.ignore_reserve_size == True -> пытаемся расшириться
                is_not_enough_free_vms = (
                    await automated_pool.check_if_not_enough_free_vms()
                )
                if self.ignore_reserve_size or is_not_enough_free_vms:
                    # Max possible amount of VMs which we can add to the pool
                    max_possible_amount_to_add = (
                        automated_pool.total_size - vm_amount_in_pool
                    )
                    # Real amount that we can add to the pool
                    real_amount_to_add = min(
                        max_possible_amount_to_add, automated_pool.increase_step
                    )
                    # add VMs.
                    try:
                        vm_list = await automated_pool.add_vm(real_amount_to_add)
                    except VmCreationError as vm_error:
                        await system_logger.error(
                            _local_("VM creating error."), description=vm_error
                        )

            # Подготовка ВМ для подключения к ТК  (под async with pool_lock)
            try:
                active_directory_object = await AuthenticationDirectory.query.where(
                    AuthenticationDirectory.status == Status.ACTIVE
                ).gino.first()

                if vm_list and automated_pool.preparation_required():
                    await asyncio.gather(
                        *[
                            vm_object.prepare_with_timeout(
                                active_directory_object, automated_pool.ad_ou, automated_pool,
                                self.task_model.creator
                            )
                            for vm_object in vm_list
                        ],
                        return_exceptions=True
                    )
            except asyncio.CancelledError:
                raise
            except Exception as E:
                await system_logger.error(
                    message=_local_("VM preparation error."), description=str(E)
                )


class RecreationGuestVmTask(AbstractTask):

    task_type = PoolTaskType.VM_GUEST_RECREATION

    def __init__(self, vm_id=None):
        super().__init__()

        self.vm_id = vm_id

    async def get_user_friendly_text(self):
        entity_name = await self._get_associated_entity_name()
        return _local_("Automatic recreation of VM {} in the guest pool.").format(entity_name)

    async def do_task(self):
        vm = await Vm.get(self.task_model.entity_id)
        automated_pool = await AutomatedPool.get(vm.pool_id)
        if not automated_pool and not automated_pool.is_guest:
            raise RuntimeError("RecreationGuestVmTask: GuestPool doesnt exist")

        vm_list = list()

        async with redis_get_lock(str(automated_pool.id)):
            async with redis_get_lock(str(automated_pool.template_id)):

                pool = await Pool.get(automated_pool.id)

                # Удаление и добавление 1 ВМ.
                try:
                    await pool.remove_vms([self.task_model.entity_id])
                    await vm.soft_delete(creator=self.task_model.creator, remove_on_controller=True)
                    vm_list = await automated_pool.add_vm(count=1)
                except VmCreationError as vm_error:
                    await system_logger.error(
                        _local_("VM creating error."), description=vm_error
                    )

            # Подготовка ВМ для подключения к ТК
            # TODO: убрать повтор кода
            try:
                active_directory_object = await AuthenticationDirectory.query.where(
                    AuthenticationDirectory.status == Status.ACTIVE
                ).gino.first()

                if vm_list and automated_pool.preparation_required():
                    await asyncio.gather(
                        *[
                            vm_object.prepare_with_timeout(
                                active_directory_object, automated_pool.ad_ou, automated_pool,
                                self.task_model.creator
                            )
                            for vm_object in vm_list
                        ],
                        return_exceptions=True
                    )
            except asyncio.CancelledError:
                raise
            except Exception as E:
                await system_logger.error(
                    message=_local_("VM preparation error."), description=str(E)
                )


class DecreasePoolTask(AbstractTask):

    task_type = PoolTaskType.POOL_DECREASE

    def __init__(self, new_total_size):
        super().__init__()

        self._new_total_size = new_total_size

    async def get_user_friendly_text(self):
        entity_name = await self._get_associated_entity_name()
        return _local_("Decreasing of pool {}.").format(entity_name)

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError("AutomatedPool doesnt exist")

        # Нужно использовать либо контекстный менедженр, либо таймаут. Иначе есть опасность
        # что лок останется залоченным
        pool_lock = redis_get_lock(str(automated_pool.id), timeout=10, blocking_timeout=0.5)
        lock_acquired = await pool_lock.acquire()
        if not lock_acquired:
            raise RuntimeError("Another task works on this pool")

        # decrease total_size
        try:
            pool = await Pool.get(automated_pool.id)
            vm_amount = await pool.get_vm_amount()
            if self._new_total_size < vm_amount:
                raise RuntimeError(
                    "Total size can not be less than current amount of VMs"
                )

            await automated_pool.update(total_size=self._new_total_size).apply()
        finally:
            await redis_release_lock_no_errors(pool_lock)


class DeletePoolTask(AbstractTask):

    task_type = PoolTaskType.POOL_DELETE

    def __init__(self, full_deletion=True):
        super().__init__()

        self.full_deletion = full_deletion
        self._task_priority = 3

    async def get_user_friendly_text(self):
        entity_name = await self._get_associated_entity_name()
        return _local_("Deleting of pool {}.").format(entity_name)

    async def do_task(self):

        await system_logger.debug("start_pool_deleting")
        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError("DeletePoolTask: AutomatedPool doesnt exist")

        # Нужно остановить таски связанные с пулом
        tasks_related_to_cur_pool = self._get_related_progressing_tasks()
        # Отменяем их
        for task in tasks_related_to_cur_pool:
            await task.cancel()

        # Лочим
        async with redis_get_lock(str(automated_pool.id)):
            # удаляем пул
            pool = await Pool.get(automated_pool.id)

            is_deleted = await Pool.delete_pool(pool, "system")
            await system_logger.debug("is pool deleted: {}".format(is_deleted))


class PrepareVmTask(AbstractTask):
    """Задача подготовки ВМ."""

    task_type = PoolTaskType.VM_PREPARE

    def __init__(self, full_preparation=True):
        super().__init__()

        self._full_preparation = (
            full_preparation
        )  # полная подготовка. Используется для машин динамического пула
        # В случае неполной подготовки только включаем удаленный доступ (для машин статик пула)

    async def get_user_friendly_text(self):
        entity_name = await self._get_associated_entity_name()
        return _local_("Preparation of vm {}.").format(entity_name)

    async def do_task(self):
        # Проверить выполняется ли уже задача подготовки этой вм. Запускать еще одну нет смысла и даже вредно.
        vm_prepare_tasks = self._get_related_progressing_tasks()
        if len(vm_prepare_tasks) > 0:
            raise RuntimeError(_local_("Another task works on this VM."))

        # preparation (код перенесен из pool/schema.py)
        vm = await Vm.get(self.task_model.entity_id)
        if vm:
            if self._full_preparation:
                await self._do_full_preparation(vm)
            else:
                await self._do_light_preparation(vm)

    async def _do_full_preparation(self, vm):
        """Full preparation."""
        pool = await Pool.get(vm.pool_id)

        pool_type = pool.pool_type
        if pool_type == Pool.PoolTypes.AUTOMATED or pool_type == Pool.PoolTypes.GUEST:
            auto_pool = await AutomatedPool.get(pool.id)
            active_directory_object = await AuthenticationDirectory.query.where(
                AuthenticationDirectory.status == Status.ACTIVE
            ).gino.first()
            ad_ou = auto_pool.ad_ou

            await vm.prepare_with_timeout(active_directory_object, ad_ou, auto_pool, self.task_model.creator)

    async def _do_light_preparation(self, vm):
        """Only remote access."""
        veil_domain = await vm.vm_client
        if not veil_domain:
            raise client_exceptions.ServerDisconnectedError()

        await veil_domain.info()

        if not veil_domain.remote_access:
            # Удаленный доступ выключен, нужно включить и ждать
            action_response = await veil_domain.enable_remote_access()

            if not action_response.success:
                # Вернуть исключение?
                raise ValueError(_local_("ECP VeiL domain request error."))
            if action_response.status_code == 200:
                # Задача не встала в очередь, а выполнилась немедленно. Такого не должно быть.
                raise ValueError(_local_("Task has`t been created."))
            if action_response.status_code == 202:
                # Была установлена задача. Необходимо дождаться ее выполнения.
                action_task = action_response.task
                await vm.task_waiting(action_task)

                # Если задача выполнена с ошибкой - прерываем выполнение
                if action_task:
                    task_success = await action_task.success
                    api_object_id = action_task.api_object_id
                else:
                    task_success = False
                    api_object_id = ""

                if not task_success:
                    raise ValueError(
                        _local_(
                            "VM remote access task {} for VM {} finished with error.").format(
                            api_object_id, vm.verbose_name
                        )
                    )


class BackupVmsTask(AbstractTask):

    task_type = PoolTaskType.VMS_BACKUP

    def __init__(self, entity_type):
        super().__init__()

        self._entity_type = entity_type

    async def get_user_friendly_text(self):
        entity_name = await self._get_associated_entity_name()
        return _local_("Backup of {}.").format(entity_name)

    async def do_task(self):

        if self._entity_type == EntityType.VM.name:
            vm = await Vm.get(self.task_model.entity_id)
            ok = await vm.backup(creator=self.task_model.creator)

        elif self._entity_type == EntityType.POOL.name:
            pool = await Pool.get(self.task_model.entity_id)
            ok = await pool.backup_vms(creator=self.task_model.creator)

        else:
            raise RuntimeError(_local_("Wrong entity type."))

        if not ok:
            raise RuntimeError(_local_("Creating backup finished with error."))


class RemoveVmsTask(AbstractTask):
    """Реализация задачи удаления ВМ из пула."""

    task_type = PoolTaskType.VMS_REMOVE

    def __init__(self, vm_ids):
        super().__init__()

        self._vm_ids = vm_ids

    async def get_user_friendly_text(self):
        entity_name = await self._get_associated_entity_name()
        return _local_("Removal of VMs from pool {}.").format(entity_name)

    async def do_task(self):
        pool = await Pool.get(self.task_model.entity_id)
        pool_type = pool.pool_type

        if pool_type == Pool.PoolTypes.AUTOMATED or pool_type == Pool.PoolTypes.GUEST:
            async with redis_get_lock(str(pool.id)):
                await self.remove_vms(pool, remove_vms_on_controller=True)
        elif pool_type == Pool.PoolTypes.STATIC:
            await self.remove_vms(pool)
        else:
            raise RuntimeError(_local_("Unsupported pool type."))

    async def remove_vms(self, pool, remove_vms_on_controller=False):
        await pool.remove_vms(self._vm_ids, self.task_model.creator)
        # remove vms from db
        await Vm.remove_vms(self._vm_ids, self.task_model.creator, remove_vms_on_controller)
