# -*- coding: utf-8 -*-
import asyncio
import traceback
from abc import ABC, abstractmethod

from aiohttp import client_exceptions

from common.languages import lang_init
from common.log.journal import system_logger
from common.models.authentication_directory import AuthenticationDirectory
from common.models.pool import AutomatedPool, Pool
from common.models.task import Task, TaskStatus
from common.models.vm import Vm
from common.utils import cancel_async_task
from common.veil.veil_errors import PoolCreationError, VmCreationError
from common.veil.veil_gino import EntityType, Status

_ = lang_init()


class AbstractTask(ABC):
    """Выполняет задачу do_task."""

    task_list = (
        list()
    )  # Список, в котором держим объекты выполняемым в данный момент таскок

    def __init__(self):

        self.task_model = None
        self._coroutine = None
        self._task_priority = 1

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
                "AbstractTask.execute: logical error. No such task"
            )
            return

        await self.task_model.update(priority=self._task_priority).apply()

        # set task status
        await self.task_model.set_status(TaskStatus.IN_PROGRESS)
        friendly_task_name = await self.task_model.form_user_friendly_text()
        await system_logger.info(_("Task '{}' started.").format(friendly_task_name))

        # Добавить себя в список выполняющихся задач
        AbstractTask.task_list.append(self)

        try:
            await self.do_task()
            await self.task_model.set_status(TaskStatus.FINISHED)
            await system_logger.info(
                _("Task '{}' finished successfully.").format(friendly_task_name)
            )

        except asyncio.CancelledError:
            await self.task_model.set_status(TaskStatus.CANCELLED)
            await system_logger.warning(
                _("Task '{}' cancelled.").format(friendly_task_name)
            )

            await self.do_on_cancel()

        except Exception as ex:  # noqa

            message = _("Task '{}' failed.").format(friendly_task_name)

            await self.task_model.set_status(TaskStatus.FAILED, message + " " + str(ex))

            # event
            tb = traceback.format_exc()
            description = str(ex) + " " + tb
            await system_logger.warning(message=message, description=description)
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


class InitPoolTask(AbstractTask):
    def __init__(self, pool_locks):
        super().__init__()

        self._pool_locks = pool_locks
        self._task_priority = 2

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError("InitPoolTask: AutomatedPool doesnt exist")

        # Создать локи (Над пулом единовременно может работать только одна таска.)
        self._pool_locks.add_new_pool_data(
            str(automated_pool.id), str(automated_pool.template_id)
        )

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))
        template_lock = self._pool_locks.get_template_lock(
            str(automated_pool.template_id)
        )

        async with pool_lock:
            async with template_lock:
                # Добавляем машины
                try:
                    pool = await Pool.get(self.task_model.entity_id)
                    await pool.update(status=Status.CREATING).apply()

                    await automated_pool.add_initial_vms()
                except PoolCreationError:
                    await automated_pool.deactivate()
                    # Чтобы проблема была передана внешнему обработчику в AbstractTask
                    raise
                except asyncio.CancelledError:
                    await system_logger.warning(_("Pool Creation cancelled."))
                    await automated_pool.deactivate()
                    raise
                except Exception as E:
                    await system_logger.error(
                        message=_("Failed to init pool."), description=str(E)
                    )
                    await automated_pool.deactivate()
                    raise E

            # Подготавливаем машины. Находимся на этом отступе так как нам нужен лок пула но не нужен лок шаблона
            try:
                if automated_pool.prepare_vms:
                    results_future = await automated_pool.prepare_initial_vms()
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
                    message=_("Pool initialization VM(s) preparation error."),
                    description=str(E),
                )
                raise E

        # Активируем пул
        await automated_pool.activate()


class ExpandPoolTask(AbstractTask):
    def __init__(self, pool_locks, ignore_reserve_size=False, wait_for_lock=True):
        super().__init__()

        self._pool_locks = pool_locks
        self.ignore_reserve_size = (
            ignore_reserve_size
        )  # расширение не смотря на достаточный резерв
        self.wait_for_lock = (
            wait_for_lock
        )  # Если true ждем освобождения локов. Если false, то бросаем исключение, если
        # локи заняты

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError("ExpandPoolTask: AutomatedPool doesnt exist")

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))
        template_lock = self._pool_locks.get_template_lock(
            str(automated_pool.template_id)
        )

        # Проверяем залочены ли локи. Если залочены, то бросаем исключение.
        # Экспериментально сделано опциональным (self.wait_for_lock)
        if not self.wait_for_lock and (pool_lock.locked() or template_lock.locked()):
            raise RuntimeError(
                "ExpandPoolTask: Another task works on this pool or vm template is busy"
            )

        vm_list = list()

        async with pool_lock:
            async with template_lock:
                # Check that total_size is not reached
                pool = await Pool.get(automated_pool.id)
                vm_amount_in_pool = await pool.get_vm_amount()

                # If reached then do nothing
                if vm_amount_in_pool >= automated_pool.total_size:
                    return

                # Если подогретых машин слишком мало, то пробуем добавить еще
                #  Если self.ignore_reserve_size==True то пытаемся расширится безусловно
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
                            _("VM creating error."), description=vm_error
                        )

            # Подготовка ВМ для подключения к ТК  (под async with pool_lock)
            try:
                active_directory_object = await AuthenticationDirectory.query.where(
                    AuthenticationDirectory.status == Status.ACTIVE
                ).gino.first()
                if vm_list and automated_pool.prepare_vms:
                    await asyncio.gather(
                        *[
                            vm_object.prepare_with_timeout(
                                active_directory_object, automated_pool.ad_cn_pattern
                            )
                            for vm_object in vm_list
                        ],
                        return_exceptions=True
                    )
            except asyncio.CancelledError:
                raise
            except Exception as E:
                await system_logger.error(
                    message=_("VM preparation error."), description=str(E)
                )


class RecreationGuestVmTask(AbstractTask):
    def __init__(self, pool_locks, vm_id=None, ignore_reserve_size=True,
                 wait_for_lock=True):
        super().__init__()

        self._pool_locks = pool_locks
        self.vm_id = vm_id
        self.ignore_reserve_size = (
            ignore_reserve_size
        )  # форсированное добавление ВМ вместо удаляемой, игнорируя резерв
        self.wait_for_lock = (
            wait_for_lock
        )  # Если true-ждем освобождения локов. Если false, то исключение-локи заняты

    async def do_task(self):
        vm = await Vm.get(self.task_model.entity_id)
        automated_pool = await AutomatedPool.get(vm.pool_id)
        if not automated_pool and not automated_pool.is_guest:
            raise RuntimeError("RecreationGuestVmTask: GuestPool doesnt exist")

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))
        template_lock = self._pool_locks.get_template_lock(
            str(automated_pool.template_id)
        )

        # Если залочены локи, то вызывается исключение.
        if not self.wait_for_lock and (pool_lock.locked() or template_lock.locked()):
            raise RuntimeError(
                "RecreationGuestVmTask: Another task works on this pool or vm template is busy"
            )

        vm_list = list()

        async with pool_lock:
            async with template_lock:
                # Проверяем, что максимальное значение ВМ в пуле не достигнуто
                pool = await Pool.get(automated_pool.id)
                # vm_amount_in_pool = await pool.get_vm_amount()
                #
                # # Если достигнуто максимальное значение ВМ в пуле, ничего не делать
                # if vm_amount_in_pool >= automated_pool.total_size:
                #     return
                #
                # # Если подогретых машин слишком мало, то пробуем добавить еще
                # #  Если self.ignore_reserve_size то пытаемся добавить ВМ безусловно
                # is_not_enough_free_vms = (
                #     await automated_pool.check_if_not_enough_free_vms()
                # )
                if self.ignore_reserve_size:
                    # Удаление и добавление 1 ВМ.
                    try:
                        vm_ids = list()
                        vm_ids.append(self.task_model.entity_id)
                        await pool.remove_vms(vm_ids)
                        await vm.soft_delete(creator="system",
                                             remove_on_controller=True)
                        vm_list = await automated_pool.add_vm(count=1)
                    except VmCreationError as vm_error:
                        await system_logger.error(
                            _("VM creating error."), description=vm_error
                        )

            # Подготовка ВМ для подключения к ТК (под async with pool_lock)
            try:
                active_directory_object = await AuthenticationDirectory.query.where(
                    AuthenticationDirectory.status == Status.ACTIVE
                ).gino.first()
                if vm_list and automated_pool.prepare_vms:
                    await asyncio.gather(
                        *[
                            vm_object.prepare_with_timeout(
                                active_directory_object, automated_pool.ad_cn_pattern
                            )
                            for vm_object in vm_list
                        ],
                        return_exceptions=True
                    )
            except asyncio.CancelledError:
                raise
            except Exception as E:
                await system_logger.error(
                    message=_("VM preparation error."), description=str(E)
                )


class DecreasePoolTask(AbstractTask):
    def __init__(self, pool_locks, new_total_size):
        super().__init__()

        self._pool_locks = pool_locks
        self._new_total_size = new_total_size

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError("AutomatedPool doesnt exist")

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))
        if pool_lock.locked():
            raise RuntimeError("Another task works on this pool")

        # decrease total_size
        async with pool_lock:
            pool = await Pool.get(automated_pool.id)
            vm_amount = await pool.get_vm_amount()
            if self._new_total_size < vm_amount:
                raise RuntimeError(
                    "Total size can not be less than current amount of VMs"
                )

            await automated_pool.update(total_size=self._new_total_size).apply()


class DeletePoolTask(AbstractTask):
    def __init__(self, pool_locks, full_deletion):
        super().__init__()

        self.full_deletion = full_deletion
        self._pool_locks = pool_locks
        self._task_priority = 3

    async def do_task(self):

        await system_logger.debug("start_pool_deleting")
        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError("DeletePoolTask: AutomatedPool doesnt exist")

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))

        # Нужно остановить таски связанные с пулом
        tasks_related_to_cur_pool = self._get_related_progressing_tasks()
        # Отменяем их
        for task in tasks_related_to_cur_pool:
            await task.cancel()

        # Лочим
        async with pool_lock:
            template_id = automated_pool.template_id
            # удаляем пул
            pool = await Pool.get(automated_pool.id)

            is_deleted = await Pool.delete_pool(pool, "system")
            await system_logger.debug("is pool deleted: {}".format(is_deleted))

            # убираем из памяти локи, если пул успешно удалился
            if is_deleted:
                await self._pool_locks.remove_pool_data(
                    str(automated_pool.id), str(template_id)
                )


class PrepareVmTask(AbstractTask):
    """Задача подготовки ВМ.

    При удалении ВМ желательно учесть что эта задача может быть в процессе выполнения и сначала отменить ее.
    """

    # TODO: refactoring
    # TODO: подключить линтеры

    def __init__(self, full_preparation=True):
        super().__init__()

        self._full_preparation = (
            full_preparation
        )  # полная подготовка. Используется для машин динамического пула
        # В случае неполной подготовки только включаем удаленный доступ (для машин статик пула)

    async def do_task(self):
        # print('!!!PrepareVmTask started', flush=True)
        # Проверить выполняется ли уже задача подготовки этой вм. Запускать еще одну нет смысла и даже вредно.
        vm_prepare_tasks = self._get_related_progressing_tasks()
        if len(vm_prepare_tasks) > 0:
            raise RuntimeError(_("Another task works on this VM."))

        # preparation (код перенесен из pool/schema.py)
        vm = await Vm.get(self.task_model.entity_id)
        if vm:
            if self._full_preparation:
                await self._do_full_preparation(vm)
            else:
                await self._do_light_preparation(vm)

    async def _do_full_preparation(self, vm):
        """Full preparation."""
        active_directory_object = None
        ad_cn_pattern = None

        pool = await Pool.get(vm.pool_id)

        pool_type = await pool.pool_type
        if pool_type == Pool.PoolTypes.AUTOMATED or pool_type == Pool.PoolTypes.GUEST:
            auto_pool = await AutomatedPool.get(pool.id)
            active_directory_object = await AuthenticationDirectory.query.where(
                AuthenticationDirectory.status == Status.ACTIVE
            ).gino.first()
            ad_cn_pattern = auto_pool.ad_cn_pattern

        await vm.prepare_with_timeout(active_directory_object, ad_cn_pattern)

    async def _do_light_preparation(self, vm):
        """Only remote access."""
        # TODO: убрать дублирование кода при подготовке
        # print('_do_light_preparation ', 'vm.id ', vm.id, flush=True)
        veil_domain = await vm.vm_client
        if not veil_domain:
            raise client_exceptions.ServerDisconnectedError()

        await veil_domain.info()

        if not veil_domain.remote_access:
            # Удаленный доступ выключен, нужно включить и ждать
            action_response = await veil_domain.enable_remote_access()

            if not action_response.success:
                # Вернуть исключение?
                raise ValueError(_("ECP VeiL domain request error."))
            if action_response.status_code == 200:
                # Задача не встала в очередь, а выполнилась немедленно. Такого не должно быть.
                raise ValueError(_("Task has`t been created."))
            if action_response.status_code == 202:
                # Была установлена задача. Необходимо дождаться ее выполнения.
                # TODO: метод ожидания задачи
                action_task = action_response.task
                task_completed = False
                while action_task and not task_completed:
                    await asyncio.sleep(5)  # VEIL_OPERATION_WAITING
                    task_completed = await action_task.is_finished()

                # Если задача выполнена с ошибкой - прерываем выполнение
                if action_task:
                    task_success = await action_task.success
                    api_object_id = action_task.api_object_id
                else:
                    task_success = False
                    api_object_id = ""

                if not task_success:
                    raise ValueError(
                        _("VM remote access task {} for VM {} finished with error.").format(
                            api_object_id, vm.verbose_name
                        )
                    )


class BackupVmsTask(AbstractTask):
    def __init__(self, entity_type, creator):
        super().__init__()

        self._entity_type = entity_type
        self._creator = creator

    async def do_task(self):

        if self._entity_type == EntityType.VM.name:
            # print('self._entity_type == EntityType.VM.name:', flush=True)
            vm = await Vm.get(self.task_model.entity_id)
            ok = await vm.backup(creator=self._creator)

        elif self._entity_type == EntityType.POOL.name:
            # print('self._entity_type == EntityType.POOL.name:', flush=True)
            pool = await Pool.get(self.task_model.entity_id)
            ok = await pool.backup_vms(creator=self._creator)

        else:
            raise RuntimeError(_("Wrong entity type."))

        if not ok:
            raise RuntimeError(_("Creating backup finished with error."))


class RemoveVmsTask(AbstractTask):
    """Реализация задачи удаления ВМ из пула."""

    def __init__(self, pool_locks, vm_ids, creator):
        super().__init__()

        self._pool_locks = pool_locks  # для сихранизации задач над динамическим пулом
        self._vm_ids = vm_ids
        self._creator = creator

    async def do_task(self):
        pool = await Pool.get(self.task_model.entity_id)
        pool_type = await pool.pool_type

        if pool_type == Pool.PoolTypes.AUTOMATED or pool_type == Pool.PoolTypes.GUEST:
            pool_lock = self._pool_locks.get_pool_lock(str(pool.id))
            async with pool_lock:
                await self.remove_vms(pool, remove_vms_on_controller=True)
        elif pool_type == Pool.PoolTypes.STATIC:
            await self.remove_vms(pool)
        else:
            raise RuntimeError(_("Unsupported pool type."))

    async def remove_vms(self, pool, remove_vms_on_controller=False):
        await pool.remove_vms(self._vm_ids, self._creator)
        # remove vms from db
        await Vm.remove_vms(self._vm_ids, self._creator, remove_vms_on_controller)
