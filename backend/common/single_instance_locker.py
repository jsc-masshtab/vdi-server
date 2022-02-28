# -*- coding: utf-8 -*-
import asyncio
import sys

from common.veil.veil_redis import redis_get_lock


class SingleInstanceLocker:
    """Лок для гарантирования запуска одного экземпляра процесса.

    Продлеваем глобальный лок, а не просто лочим на бесконечное время.
    Для того чтобы лок не повис залоченным в случае смерти процесса.
    """

    def __init__(self, lock_name):
        self._app_lock = None
        self._lock_name = lock_name

    async def lock(self):
        self._app_lock = redis_get_lock(name=self._lock_name, timeout=30)

        lock_acquired = await self._app_lock.acquire(blocking=False)
        if lock_acquired:
            loop = asyncio.get_event_loop()
            loop.create_task(self._keep_reacquiring())
        else:
            sys.exit("Lock is busy")

    async def unlock(self):
        if self._app_lock:
            await self._app_lock.release()

    async def _keep_reacquiring(self):

        while True:
            ext_time = 25
            await asyncio.sleep(ext_time)
            await self._app_lock.release()
            await self._app_lock.acquire(blocking=False)
