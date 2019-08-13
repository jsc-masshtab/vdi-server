from cached_property import cached_property as cached

import asyncpg
from functools import wraps

from asyncpg.connection import Connection

from contextlib import asynccontextmanager

class DbApp:
    cache = {}

    async def init(self):
        if hasattr(self, 'pool'):
            return
        self.pool = await asyncpg.create_pool(database='vdi',
                                      user='postgres')

    @asynccontextmanager
    async def transaction(self) -> Connection:
        async with self.pool.acquire() as c:
            async with c.transaction():
                yield c

    @asynccontextmanager
    async def connect(self) -> Connection:
        async with self.pool.acquire() as c:
            yield c




db = DbApp()