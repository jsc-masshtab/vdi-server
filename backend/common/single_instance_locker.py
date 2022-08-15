# -*- coding: utf-8 -*-
import asyncio

from yaaredis.exceptions import LockError

from common.veil.veil_redis import redis_get_client


class SingleInstanceLocker:
    """Лок для гарантирования запуска одного экземпляра процесса.

    Продлеваем глобальный лок, а не просто лочим на бесконечное время.
    Для того чтобы лок не повис залоченным в случае смерти процесса.
    """

    def __init__(self, lock_name):
        self._app_lock = None
        self._lock_name = lock_name

    async def lock(self):
        self._app_lock = redis_get_client().lock(name=self._lock_name, timeout=20)

        # Acquire lock and keep reacquiring
        await self._app_lock.acquire()
        loop = asyncio.get_event_loop()
        loop.create_task(self._keep_reacquiring())

    async def unlock(self):
        if self._app_lock:
            await self._app_lock.release()

    async def _keep_reacquiring(self):

        try:
            while True:
                reacquiring_timeout = 15
                await asyncio.sleep(reacquiring_timeout)
                # print("Before self.reacquire()", flush=True)
                await redis_get_client().reacquire(self._app_lock)
                # print("After self.reacquire()", flush=True)
        except LockError as ex:
            loop = asyncio.get_event_loop()
            loop.stop()
            print(f"Event loop was stopped. {str(ex)}", flush=True)
