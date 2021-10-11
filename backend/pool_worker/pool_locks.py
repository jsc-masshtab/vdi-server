# -*- coding: utf-8 -*-
import asyncio

from common.models.pool import AutomatedPool


class PoolLocks:
    """Агрегирует локи пулов и шаблонов.

    Лок пула используется для обеспечения работы над пулом только одной таски единовременно.
    Лок шаблона диктуется ограничением контролера (Единовременно из шаблона может создаваться только одна вм
    и следовательно только один пул)
    Обязательно соблюдать один и тот же порядок лока, иначе дед лок.
    """

    def __init__(self):
        self._pool_lock_dict = dict()  # словарь пул id <-> PoolLock
        self._template_lock_dict = dict()  # словарь шаблон id <-> TemplateLock

    def get_pool_lock(self, pool_id: str):

        if pool_id not in self._pool_lock_dict:
            self._pool_lock_dict[pool_id] = asyncio.Lock()

        return self._pool_lock_dict[pool_id]

    def get_template_lock(self, template_id: str):

        if template_id not in self._template_lock_dict:
            self._template_lock_dict[template_id] = asyncio.Lock()

        return self._template_lock_dict[template_id]

    async def remove_pool_data(self, pool_id: str, template_id: str):
        """Удалям локи из памяти. Используется после удаления пула."""
        if pool_id in self._pool_lock_dict:
            del self._pool_lock_dict[pool_id]

        if template_id in self._template_lock_dict:
            # Нужно проверить: может ли этот лок шаблона использоваться каким-то другим пулом кроме удаляемого
            # пула и удалить, если не используется
            is_used = await AutomatedPool.select("template_id").where(
                AutomatedPool.template_id == template_id).gino.first()

            if not is_used:
                del self._template_lock_dict[template_id]


pool_locks = PoolLocks()
