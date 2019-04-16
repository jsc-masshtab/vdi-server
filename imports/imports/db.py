

import asyncpg
from functools import wraps

from asyncpg.connection import Connection

from contextlib import asynccontextmanager

# from abc import ABC
#
# class Connection(ABC):
#     pass
#
# Connection.register()

from settings import db as db_settings

class DbApp:

    async def init(self):
        self.pool = await asyncpg.create_pool(**db_settings)

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