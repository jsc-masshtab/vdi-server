# -*- coding: utf-8 -*-
import asyncio

from yaaredis.exceptions import LockError

from common.veil.veil_redis import redis_get_client, redis_get_lock

# Добавляем скрипт для для REACQUIRE, так как его нет в редис клиенте
# KEYS[1] - lock name
# ARGV[1] - token
# ARGV[2] - milliseconds
# return 1 if the locks time was reacquired, otherwise 0
LUA_REACQUIRE_SCRIPT = """
    local token = redis.call('get', KEYS[1])
    if not token or token ~= ARGV[1] then
        return 0
    end
    redis.call('pexpire', KEYS[1], ARGV[2])
    return 1
"""


class SingleInstanceLocker:
    """Лок для гарантирования запуска одного экземпляра процесса.

    Продлеваем глобальный лок, а не просто лочим на бесконечное время.
    Для того чтобы лок не повис залоченным в случае смерти процесса.
    """

    def __init__(self, lock_name):
        self._app_lock = None
        self._lock_name = lock_name
        self._lua_reacquire = None

    async def lock(self):
        self._app_lock = redis_get_lock(name=self._lock_name, timeout=20)
        # add reacquire support
        self._lua_reacquire = redis_get_client().register_script(LUA_REACQUIRE_SCRIPT)

        # Acquire lock and keep reacquiring
        await self._app_lock.acquire()
        loop = asyncio.get_event_loop()
        loop.create_task(self._keep_reacquiring())

    async def unlock(self):
        if self._app_lock:
            await self._app_lock.release()

    async def reacquire(self):
        """Reset a TTL of an already acquired lock back to a timeout value."""
        if self._app_lock.local.get() is None:
            raise LockError("Cannot reacquire an unlocked lock")
        if self._app_lock.timeout is None:
            raise LockError("Cannot reacquire a lock with no timeout")

        timeout = int(self._app_lock.timeout * 1000)
        if not bool(
            await self._lua_reacquire.execute(
                keys=[self._app_lock.name],
                args=[self._app_lock.local.get(), timeout],
                client=self._app_lock.redis
            )
        ):
            raise LockError("Cannot extend a lock that's no longer owned")
        return True

    async def _keep_reacquiring(self):

        while True:
            reacquiring_timeout = 15
            await asyncio.sleep(reacquiring_timeout)
            # print("Before self.reacquire()", flush=True)
            await self.reacquire()
            # print("After self.reacquire()", flush=True)
