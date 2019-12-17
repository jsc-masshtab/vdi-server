import asyncio

from database import db, Status

from common.utils import cancel_async_task


class PoolLock:

    def __init__(self):
        self.lock = asyncio.Lock()

        self.create_pool_task = None  # корутина в которой пул создается
        self.expand_pool_task = None  # корутина в которой пул расширяется
        self.decrease_pool_task = None  # корутина в которой количество машин в пуле уменьшается


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
        print("self")

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
            print(__class__.__name__, 'Logic error: no such pool')
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

    # PRIVATE METHODS
    async def _get_pools_data_from_db(self):
        from pool.models import AutomatedPool
        auto_pools_data = await db.select([AutomatedPool.automated_pool_id, AutomatedPool.template_id]).\
            select_from(AutomatedPool).gino.all()
        return auto_pools_data

    def _add_data(self, pool_id: str, template_id: str):
        self._pool_lock_dict[pool_id] = PoolLock()
        if template_id not in self._template_lock_dict:
            self._template_lock_dict[template_id] = TemplateLock()


pool_task_manager = PoolTaskManager()
