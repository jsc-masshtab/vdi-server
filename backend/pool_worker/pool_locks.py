# -*- coding: utf-8 -*-
import asyncio

from common.database import db
from common.languages import lang_init


_ = lang_init()


class PoolLocks:
    """Агрегирует локи пулов и шаблонов.
    Лок пула используется для обеспечения работы над пулом только одной таски единовременно.
    Лок шаблона диктуется ограничением контролера (Единовременно из шаблона может создаваться только одна вм
    и следовательно только один пул)
    Обязательно соблюдать один и тот же порядок лока, иначе дед лок"""

    def __init__(self):
        self._pool_lock_dict = dict()  # словарь пул id <-> PoolLock
        self._template_lock_dict = dict()  # словарь шаблон id <-> TemplateLock

    def get_pool_lock(self, pool_id: str):
        # print('pool_id', pool_id)
        # print('self._pool_lock_dict', self._pool_lock_dict)
        return self._pool_lock_dict[pool_id]

    def get_template_lock(self, template_id: str):
        return self._template_lock_dict[template_id]

    async def fill_start_data(self):
        """При старте VDI заполняем _pool_lock_dict (создаем pool lock для каждого пула), заполняем
           _template_lock_dict (создаем template lock для каждого использованного шаблона)."""
        # get data from db
        auto_pools_data = await self._get_pools_data_from_db()

        # create locks
        for pool_id, template_id in auto_pools_data:
            self._add_data(str(pool_id), str(template_id))

    def add_new_pool_data(self, pool_id: str, template_id: str):
        """"При добавлении нового пула добавляем его локи в _pool_lock_dict. Смотрим есть ли
            лок шаблона в _template_lock_dict."""
        self._add_data(pool_id, template_id)

    async def remove_pool_data(self, pool_id: str, template_id: str):
        """Удалям локи из пямяти. Испоьзуется послке удаления пула"""
        del self._pool_lock_dict[pool_id]

        # Нужно проверить: использует ли этот шаблон еще кто-то кроме удаляемого пула и удалить, если не импользуется
        auto_pools_data = await self._get_pools_data_from_db()
        template_ids_list = [str(template_id) for _, template_id in auto_pools_data]

        if template_id not in template_ids_list:
            del self._template_lock_dict[template_id]

    async def _get_pools_data_from_db(self):
        from common.models.pool import AutomatedPool
        auto_pools_data = await db.select([AutomatedPool.id, AutomatedPool.template_id]).\
            select_from(AutomatedPool).gino.all()
        return auto_pools_data

    def _add_data(self, pool_id: str, template_id: str):
        """Создает локи для пула и шаблона"""
        if pool_id not in self._pool_lock_dict:
            self._pool_lock_dict[pool_id] = asyncio.Lock()
        if template_id not in self._template_lock_dict:
            self._template_lock_dict[template_id] = asyncio.Lock()
