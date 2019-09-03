import asyncio

import asyncpg

from asyncpg.connection import Connection

from contextlib import asynccontextmanager

class DbApp:
    pool = None

    async def get_pool(self):
        if self.pool is not None:
            return self.pool
        return await asyncpg.create_pool(database='vdi', user='postgres')

    @asynccontextmanager
    async def transaction(self) -> Connection:
        if self.pool is None:
            self.pool = await self.get_pool()
        async with self.pool.acquire() as c:
            async with c.transaction():
                yield c

    @asynccontextmanager
    async def connect(self) -> Connection:
        if self.pool is None:
            self.pool = await self.get_pool()
        async with self.pool.acquire() as c:
            yield c



db = DbApp()

async def fetch(*query):
    async with db.connect() as conn:
        return await conn.fetch(*query)