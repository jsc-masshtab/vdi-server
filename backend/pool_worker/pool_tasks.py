# -*- coding: utf-8 -*-
import asyncio
import traceback

from common.veil.veil_errors import PoolCreationError

from common.log.journal import system_logger
from common.veil.veil_errors import VmCreationError

from common.veil.veil_gino import EntityType, Status

from common.utils import cancel_async_task

from common.languages import lang_init

from common.models.pool import AutomatedPool, Pool
from common.models.task import TaskStatus, Task
from common.models.authentication_directory import AuthenticationDirectory


_ = lang_init()


class AbstractTask:
    """Выполняет задачу do_task"""

    def __init__(self):

        self.task_model = None
        self._coroutine = None
        self._ref_to_task_list = None  # Сссылка на список обьектов задач. Сам список живет в классе PoolTaskManager
        # Введено из-за нежелания создавать глобальную переменную task_list.
        self._task_priority = 1

    async def init(self, task_id, task_list):
        self._ref_to_task_list = task_list
        self.task_model = await Task.get(task_id)

        if self.task_model:
            await self.task_model.update(priority=self._task_priority).apply()

    async def cancel(self, resumable=False, wait_for_result=True):
        """Отменить таску"""
        if self.task_model:
            await self.task_model.update(resumable=resumable).apply()

        if self._coroutine:
            await system_logger.debug('cancel self.coroutine {}'.format(self._coroutine))
            await cancel_async_task(self._coroutine, wait_for_result)
            self._coroutine = None

    async def do_task(self):
        """Корутина, в которой будет выполняться таска"""
        raise NotImplementedError

    async def do_on_cancel(self):
        """Действия при отмене корутины do_task"""
        pass

    async def do_on_fail(self):
        """Действия при фэйле корутины do_task"""
        pass

    async def execute(self):
        """Выполнить корутину do_task"""

        if not self.task_model:
            await system_logger.error('AbstractTask.execute: logical error. No such task')
            return

        await system_logger.debug('Start task execution: {}'.format(self.task_model.task_type.name))

        # Добавить себя в список выполняющихся задач
        self._ref_to_task_list.append(self)
        # set task status
        await self.task_model.set_status(TaskStatus.IN_PROGRESS)

        try:
            await self.do_task()
            await self.task_model.set_status(TaskStatus.FINISHED)

        except asyncio.CancelledError:
            await self.task_model.set_status(TaskStatus.CANCELLED)
            await system_logger.warning('Task cancelled. id: {}'.format(self.task_model.id))

            await self.do_on_cancel()

        except Exception as ex:  # noqa
            message = 'Exception during task execution. id: {} exception: {} '.format(self.task_model.id, str(ex))
            await self.task_model.set_status(TaskStatus.FAILED, message)

            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            await system_logger.warning(message, entity=entity)
            print('BT {bt}'.format(bt=traceback.format_exc()))

            await self.do_on_fail()

        finally:
            # Удалить себя из списка выполняющихся задач
            self._ref_to_task_list.remove(self)

    def execute_in_async_task(self):
        """Запустить корутину асинхронно"""
        self._coroutine = asyncio.get_event_loop().create_task(self.execute())


class InitPoolTask(AbstractTask):

    def __init__(self, pool_locks):
        super().__init__()

        self._pool_locks = pool_locks
        self._task_priority = 2

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError('InitPoolTask: AutomatedPool doesnt exist')

        # Создать локи (Над пулом единовременно может работать только одна таска.)
        self._pool_locks.add_new_pool_data(str(automated_pool.id), str(automated_pool.template_id))

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))
        template_lock = self._pool_locks.get_template_lock(str(automated_pool.template_id))

        # todo: Если захотеть,то еще можно посмотреть занят ли шаблон тасками расширения пулов. И если занят,
        # то отменить эти таски как незначительные по сравнению с желанием создать новый пул.

        # лочим
        async with pool_lock:
            async with template_lock:
                # Добавляем машины
                try:
                    pool = await Pool.get(self.task_model.entity_id)
                    await pool.update(status=Status.CREATING).apply()

                    await automated_pool.add_initial_vms()
                except PoolCreationError:
                    await automated_pool.deactivate()
                    raise  # Чтобы проблема была передана внешнему обработчику в AbstractTask
                except asyncio.CancelledError:
                    await system_logger.debug(_('Pool Creation cancelled.'))
                    await automated_pool.deactivate()
                    raise
                except Exception as E:
                    await system_logger.error(message=_('Failed to init pool.'),
                                              description=str(E))
                    await automated_pool.deactivate()
                    raise E

            # Подготавливаем машины. Находимся на этом отступе так как нам нужен лок пула но не нужен лок шаблона
            try:
                if automated_pool.prepare_vms:
                    await automated_pool.prepare_initial_vms()
            except asyncio.CancelledError:
                await automated_pool.deactivate()
                raise
            except Exception as E:
                await system_logger.error(message=_('Virtual machine(s) preparation error.'), description=str(E))

        # Активируем пул
        await automated_pool.activate()


class ExpandPoolTask(AbstractTask):

    def __init__(self, pool_locks, ignore_reserve_size=False, wait_for_lock=False):
        super().__init__()

        self._pool_locks = pool_locks
        self.ignore_reserve_size = ignore_reserve_size  # расширение не смотря на достаточный резерв
        self.wait_for_lock = wait_for_lock  # Если true ждем освобождеия локов. Если false, то бросаем исключение, если
        # локи заняты

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError('ExpandPoolTask: AutomatedPool doesnt exist')

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))
        template_lock = self._pool_locks.get_template_lock(str(automated_pool.template_id))

        # Проверяем залочены ли локи. Если залочены, то бросаем исключение.
        # Экспериментально сделано опциальным (self.wait_for_lock)
        if not self.wait_for_lock and (pool_lock.locked() or template_lock.locked()):
            raise RuntimeError('ExpandPoolTask: Another task works on this pool or vm template is busy')

        vm_list = list()

        async with pool_lock:
            async with template_lock:
                # Check that total_size is not reached
                pool = await Pool.get(automated_pool.id)
                vm_amount_in_pool = await pool.get_vm_amount()

                # If reached then do nothing
                if vm_amount_in_pool >= automated_pool.total_size:
                    return

                # Число машин в пуле, неимеющих пользователя
                free_vm_amount = await pool.get_vm_amount(only_free=True)
                # print('!!!free_vm_amount: ', free_vm_amount, flush=True)
                # print('!!!automated_pool.increase_step: ', automated_pool.increase_step, flush=True)

                # Если подогретых машин слишком мало, то пробуем добавить еще
                #  Если self.ignore_reserve_size==True то пытаемся расширится безусловно
                if self.ignore_reserve_size or (free_vm_amount <= automated_pool.reserve_size):
                    # Max possible amount of VMs which we can add to the pool
                    max_possible_amount_to_add = automated_pool.total_size - vm_amount_in_pool
                    # Real amount that we can add to the pool
                    real_amount_to_add = min(max_possible_amount_to_add, automated_pool.increase_step)
                    # add VMs.
                    try:

                        for i in range(0, real_amount_to_add):  # noqa
                            vm_object = await automated_pool.add_vm()
                            vm_list.append(vm_object)
                    except VmCreationError as vm_error:
                        await system_logger.error(_('VM creating error.'))
                        await system_logger.debug(vm_error)

            # Подготовка ВМ для подключения к ТК  (под async with pool_lock)
            try:
                active_directory_object = await AuthenticationDirectory.query.where(
                    AuthenticationDirectory.status == Status.ACTIVE).gino.first()
                if vm_list and automated_pool.prepare_vms:
                    await asyncio.gather(
                        *[vm_object.prepare_with_timeout(active_directory_object, automated_pool.ad_cn_pattern) for
                          vm_object in vm_list])
            except asyncio.CancelledError:
                raise
            except Exception as E:
                await system_logger.error(message=_('VM preparation error.'), description=str(E))


class DecreasePoolTask(AbstractTask):

    def __init__(self, pool_locks, new_total_size):
        super().__init__()

        self._pool_locks = pool_locks
        self.new_total_size = new_total_size

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError('AutomatedPool doesnt exist')

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))
        if pool_lock.locked():
            raise RuntimeError('Another task works on this pool')

        # decrease total_size
        async with pool_lock:
            pool = await Pool.get(automated_pool.id)
            vm_amount = await pool.get_vm_amount()
            if self.new_total_size < vm_amount:
                raise RuntimeError('Total size can not be less than current amount of VMs')

            await automated_pool.update(total_size=self.new_total_size).apply()


class DeletePoolTask(AbstractTask):

    def __init__(self, pool_locks, full_deletion):
        super().__init__()

        self.full_deletion = full_deletion
        self._pool_locks = pool_locks
        self._task_priority = 3

    async def do_task(self):

        await system_logger.debug('start_pool_deleting')
        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            raise RuntimeError('DeletePoolTask: AutomatedPool doesnt exist')

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))

        # Нужно остановить таски связанные с пулом
        # print('Before cancelling in pool deletion ', len(self._ref_to_task_list))  # temp
        # Находим таски связанные с текущим пулом (исключая текущую таску)
        tasks_related_to_cur_pool = [task for task in self._ref_to_task_list
                                     if task.task_model.entity_id == self.task_model.entity_id  # noqa
                                     and task.task_model.id != self.task_model.id]  # noqa
        # Отменяем их
        for task in tasks_related_to_cur_pool:
            await task.cancel()
        # print('After cancelling in pool deletion', len(self._ref_to_task_list))  # temp

        # Лочим
        async with pool_lock:
            template_id = automated_pool.template_id
            # удаляем пул
            pool = await Pool.get(automated_pool.id)

            is_deleted = await Pool.delete_pool(pool, 'system')
            await system_logger.debug('is pool deleted: {}'.format(is_deleted))

            # убираем из памяти локи, если пул успешно удалился
            if is_deleted:
                await self._pool_locks.remove_pool_data(str(automated_pool.id), str(template_id))
