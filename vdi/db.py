from cached_property import cached_property as cached

import asyncpg
from functools import wraps

from typed_contextmanager import typed_contextmanager

from asyncpg.connection import Connection

# from abc import ABC
#
# class Connection(ABC):
#     pass
#
# Connection.register()

class DbApp:

    async def init(self):
        self.pool = await asyncpg.create_pool(database='vdi',
                                      user='postgres')

    @typed_contextmanager
    async def transaction(self) -> Connection:
        async with self.pool.acquire() as c:
            async with c.transaction():
                yield c

    @typed_contextmanager
    async def connect(self) -> Connection:
        async with self.pool.acquire() as c:
            yield c



db = DbApp()