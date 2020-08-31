# -*- coding: utf-8 -*-
import asyncio
import json
import traceback

from common.veil.veil_errors import PoolCreationError

from common.log.journal import system_logger

from common.models.pool import AutomatedPool, Pool

from common.veil.veil_errors import VmCreationError, SimpleError

from common.veil.veil_redis import REDIS_CLIENT, INTERNAL_EVENTS_CHANNEL
from common.veil.veil_gino import EntityType
from web_app.front_ws_api.subscription_sources import VDI_TASKS_SUBSCRIPTION

from common.utils import cancel_async_task

from common.languages import lang_init

from common.models.tasks import TaskStatus, TaskModel


_ = lang_init()


class AbstractTask:
    """Выполняет задачу do_task"""

    def __init__(self):

        self.task_model = None
        self._coroutine = None
        self._ref_to_task_list = None  # Сссылка на список обьектов задач. Сам список живет в классе PoolTaskManager
        # Введено из-за нежелания создавать глобальную переменную task_list. todo: made it weakref!
        self._task_priority = 1

    async def init(self, task_id, task_list):
        self._ref_to_task_list = task_list
        self.task_model = await TaskModel.get(task_id)

        if self.task_model:
            await self.task_model.update(priority=self._task_priority).apply()

    async def cancel(self, resume_on_app_startup=False):
        """Отменить таску"""
        if self.task_model:
            await self.task_model.update(resume_on_app_startup=resume_on_app_startup).apply()

        await system_logger.debug('cancel self.coroutine {}'.format(self._coroutine))
        await cancel_async_task(self._coroutine)
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

    async def do_on_finish(self):
        """Действия после завершения корутины do_task"""
        pass

    async def execute(self):
        """Выполнить корутину do_task"""

        if not self.task_model:
            await system_logger.error('AbstractTask.execute: logical error. No such task')
            return

        await system_logger.debug('Start task execution: {}'.format(self.task_model.task_type))

        # Добавить себя в список выполняющихся задач
        self._ref_to_task_list.append(self)

        await self.task_model.set_status(TaskStatus.IN_PROGRESS)

        try:
            await self.do_task()
            await self.task_model.set_status(TaskStatus.FINISHED)

        except asyncio.CancelledError:
            await self.task_model.set_status(TaskStatus.CANCELLED)
            await system_logger.warning('Task cancelled. id: {}'.format(self.task_model.id))

            await self.do_on_cancel()

        except Exception as ex:  # noqa
            await self.task_model.set_status(TaskStatus.FAILED)
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            await system_logger.warning(
                'Exception during task execution. id: {} exception: {} '.format(self.task_model.id, str(ex)),
                entity=entity)
            print('BT {bt}'.format(bt=traceback.format_exc()))

            await self.do_on_fail()

        finally:
            await self.do_on_finish()

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

    def __del__(self):
        system_logger._debug('In destructor InitPoolTask')

    async def do_task(self):

        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            return

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
                    await automated_pool.add_initial_vms()
                except PoolCreationError:
                    await system_logger.debug('Pool Creation cancelled')
                    await automated_pool.deactivate()
                except asyncio.CancelledError:
                    await automated_pool.deactivate()
                    raise
                except Exception as E:
                    await system_logger.error('Failed to create pool. {exception} {name}'.format(
                        exception=str(E), name=E.__class__.__name__))
                    await automated_pool.deactivate()
                    raise E
                else:
                    await automated_pool.activate()


class ExpandPoolTask(AbstractTask):

    def __init__(self, pool_locks):
        super().__init__()

        self._pool_locks = pool_locks

    def __del__(self):
        print('In destructor ExpandPoolTask')  # Temp

    async def do_task(self):

        await system_logger.debug('start_pool_expanding')
        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            return

        pool_lock = self._pool_locks.get_pool_lock(str(automated_pool.id))
        template_lock = self._pool_locks.get_template_lock(str(automated_pool.template_id))

        # Проверяем залочены ли локи. Если залочены, то ничего не делаем, так как любые другие действия с
        # пулом требующие блокировки - в приоретете.
        if pool_lock.locked() or template_lock.locked():
            return

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

                # Если подогретых машин слишком мало, то пробуем добавить еще
                # Условие расширения изменено. Первое условие было < - тестируем.
                if free_vm_amount <= automated_pool.reserve_size:
                    # Max possible amount of VMs which we can add to the pool
                    max_possible_amount_to_add = automated_pool.total_size - vm_amount_in_pool
                    # Real amount that we can add to the pool
                    real_amount_to_add = min(max_possible_amount_to_add, automated_pool.increase_step)
                    # add VMs.
                    try:
                        for i in range(0, real_amount_to_add):  # noqa
                            await automated_pool.add_vm()
                    except VmCreationError as vm_error:
                        await system_logger.error(_('VM creating error:'))
                        await system_logger.debug(vm_error)


class DeletePoolTask(AbstractTask):

    def __init__(self, full_deletion, pool_locks):
        super().__init__()

        self.full_deletion = full_deletion
        self._pool_locks = pool_locks
        self._task_priority = 3

    def __del__(self):
        system_logger._debug('In destructor DeletePoolTask')

    async def do_task(self):

        await system_logger.debug('start_pool_deleting')
        automated_pool = await AutomatedPool.get(self.task_model.entity_id)
        if not automated_pool:
            return

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
            # print('pool = await Pool.get(automated_pool.id)', pool)
            try:
                is_deleted = await Pool.delete_pool(pool, 'system', self.full_deletion)
            except SimpleError as ex:
                is_deleted = False
                await system_logger.debug(str(ex))

            await system_logger.debug('is pool deleted: {}'.format(is_deleted))

            # убираем из памяти локи, если пул успешно удалился
            if is_deleted:
                await self._pool_locks.remove_pool_data(str(automated_pool.id), str(template_id))

        # publish result
        msg_dict = dict(msg=_('Deleted pool {}').format(automated_pool.id),
                        mgs_type='data',
                        event='pool_deleted',
                        pool_id=str(automated_pool.id),
                        is_successful=is_deleted,
                        resource=VDI_TASKS_SUBSCRIPTION)
        REDIS_CLIENT.publish(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))
