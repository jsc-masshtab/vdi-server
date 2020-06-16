# -*- coding: utf-8 -*-
import asyncio

from database import db
from common.utils import cancel_async_task

from languages import lang_init

from common.veil_errors import VmCreationError, PoolCreationError

from pool.models import AutomatedPool, Pool

from journal.journal import Log as log


_ = lang_init()


class PoolLock:

    def __init__(self):
        self.lock = asyncio.Lock()

        self.create_pool_task = None  # корутина в которой пул создается
        self.expand_pool_task = None  # корутина в которой пул расширяется
        self.decrease_pool_task = None  # корутина в которой количество машин в пуле уменьшается
        self.delete_pool_task = None # удаление пула


class TemplateLock:

    def __init__(self):
        self.lock = asyncio.Lock()


class PoolTaskManager:
    """Обязательно соблюдать один и тот же порядок лока, иначе дед лок"""

    def __init__(self):
        self._pool_lock_dict = dict()  # словарь пул id <-> PoolLock
        self._template_lock_dict = dict()  # словарь шаблон id <-> TemplateLock

    def get_pool_lock(self, pool_id: str):
        # print('pool_id', pool_id)
        # print('self._pool_lock_dict', self._pool_lock_dict)
        return self._pool_lock_dict[pool_id]

    def get_template_lock(self, template_id: str):
        return self._template_lock_dict[template_id]

    # PUBLIC METHODS
    async def fill_start_data(self):
        """При старте VDI заполняем pool_object_dict (создаем PoolObject для каждого пула), заполняем
           template_object_dict (создаем TemplateObject для каждого использованного шаблона)."""
        # get data from db
        auto_pools_data = await self._get_pools_data_from_db()

        # create locks
        for pool_id, template_id in auto_pools_data:
            self._add_data(str(pool_id), str(template_id))

    async def stop_all_tasks(self):
        """Управляемо остановить все таски при завершении приложения"""
        pass

    def add_new_pool_data(self, pool_id: str, template_id: str):
        """"При добавлении нового пула добавляем его в pool_object_dict. Смотрим есть ли шаблон в template_object_dict.
            Если нету, то добавляем его туда. Лочим пул(на всяк. случай) Лочим шаблон.
            В теории мы может начать ждать на локе шаблона,
            если кто-то в данный момент использует этот шаблон для расширения либо создания пула.
            Причем кто-то еще  может стоять в очереди на этот шаблон. Вот так вот."""
        self._add_data(pool_id, template_id)

    async def cancel_all_tasks_for_pool(self, pool_id: str):
        """Завершить все таски, связанные с пулом"""
        if pool_id not in self._pool_lock_dict:
            print(__class__.__name__, _('Logic error: no such pool'))
            return

        cur_pool_lock = self._pool_lock_dict[pool_id]

        await cancel_async_task(cur_pool_lock.create_pool_task)
        await cancel_async_task(cur_pool_lock.expand_pool_task)
        await cancel_async_task(cur_pool_lock.decrease_pool_task)

    async def remove_pool_data(self, pool_id: str, template_id: str):
        """При удаление какого-либо пула отменяем таски, лочим PoolObject.lock,
           удаляем пул, убираем его из pool_object_dict. Смотрим используется ли шаблон удаляемого пула в других пулах.
           Если не используется, то удаляем его из template_object_dict."""
        del self._pool_lock_dict[pool_id]

        # Нужно проверить: использует ли этот шаблон еще кто-то кроме удаляемого пула и удалить, если не импользуется
        auto_pools_data = await self._get_pools_data_from_db()
        template_ids_list = [str(template_id) for _, template_id in auto_pools_data]

        if template_id not in template_ids_list:
            del self._template_lock_dict[template_id]

    # CREATION
    async def start_pool_initialization(self, pool_id):
        log.debug('start_pool_initialization')
        automated_pool = await AutomatedPool.get(pool_id)
        # add data for protection
        self.add_new_pool_data(str(automated_pool.id), str(automated_pool.template_id))
        # start task
        pool_lock = self.get_pool_lock(pool_id)
        native_loop = asyncio.get_event_loop()
        pool_lock.create_pool_task = native_loop.create_task(self.initialization_pool_task(automated_pool))

    async def initialization_pool_task(self, automated_pool):
        """Создание на пуле виртуальных машин по параметрам пула."""
        # locks
        async with self.get_pool_lock(str(automated_pool.id)).lock:
            async with self.get_template_lock(str(automated_pool.template_id)).lock:
                try:
                    await automated_pool.add_initial_vms()
                except PoolCreationError as E:
                    await log.error('{exception}'.format(exception=str(E)))
                    await automated_pool.deactivate()
                else:
                    await automated_pool.activate()

    # EXPANDING
    async def start_pool_expanding(self, pool_id):

        automated_pool = await AutomatedPool.get(pool_id)
        pool_lock = self.get_pool_lock(pool_id)
        template_lock = self.get_template_lock(str(automated_pool.template_id))
        # Проверяем залочены ли локи. Если залочены, то ничего не делаем, так как любые другие действия с
        # пулом требующие блокировки - в приоретете.
        if not pool_lock.lock.locked() and not template_lock.lock.locked():
            async with pool_lock.lock:
                native_loop = asyncio.get_event_loop()
                pool_lock.expand_pool_task = native_loop.create_task(self.expanding_pool_task(automated_pool))

    async def expanding_pool_task(self, automated_pool):
        """
        Корутина расширения автом. пула
        Check and expand pool if required
        :return:
        """
        async with self.get_pool_lock(str(automated_pool.id)).lock:
            async with self.get_template_lock(str(automated_pool.template_id)).lock:
                # TODO: код перенесен, чтобы работал. Принципиально не перерабатывался.
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
                if free_vm_amount <= automated_pool.reserve_size and \
                        free_vm_amount <= automated_pool.min_free_vms_amount:
                    # Max possible amount of VMs which we can add to the pool
                    max_possible_amount_to_add = automated_pool.total_size - vm_amount_in_pool
                    # Real amount that we can add to the pool
                    real_amount_to_add = min(max_possible_amount_to_add, automated_pool.increase_step)
                    # add VMs.
                    try:
                        for i in range(0, real_amount_to_add):
                            domain_index = vm_amount_in_pool + i
                            await automated_pool.add_vm(domain_index)
                    except VmCreationError as vm_error:
                        await log.error(_('VM creating error:'))
                        log.debug(vm_error)

    # DELETING
    async def start_pool_deleting(self, pool_id, full):

        automated_pool = await AutomatedPool.get(pool_id)

        pool_lock = self.get_pool_lock(pool_id)
        native_loop = asyncio.get_event_loop()
        pool_lock.delete_pool_task = native_loop.create_task(self.deleting_pool_task(automated_pool, full))

    async def deleting_pool_task(self, automated_pool, full):
        """Корутина, в котрой пул удаляется"""

        # Останавливаем таски связанные с пулом
        await self.cancel_all_tasks_for_pool(str(automated_pool.id))

        # Получаем лок
        pool_lock = self.get_pool_lock(str(automated_pool.id))

        # Лочим
        async with pool_lock.lock:
            template_id = automated_pool.template_id
            # удаляем пул
            pool = await Pool.get(automated_pool.id)
            is_deleted = await Pool.delete_pool(pool, full)
            print('is_deleted: ', is_deleted)
            # убираем из памяти локи
            await self.remove_pool_data(str(automated_pool.id), str(template_id))

            # todo: publish result?

    # PRIVATE METHODS
    async def _get_pools_data_from_db(self):
        from pool.models import AutomatedPool
        auto_pools_data = await db.select([AutomatedPool.id, AutomatedPool.template_id]).\
            select_from(AutomatedPool).gino.all()
        return auto_pools_data

    def _add_data(self, pool_id: str, template_id: str):
        self._pool_lock_dict[pool_id] = PoolLock()
        if template_id not in self._template_lock_dict:
            self._template_lock_dict[template_id] = TemplateLock()

