import asyncio

import asyncpg

from asyncpg.connection import Connection

#from contextlib import asynccontextmanager # 3.7
from async_generator import async_generator, yield_, asynccontextmanager

class DbApp:
    pool = None

    async def get_pool(self):
        if self.pool is not None:
            return self.pool
        return await asyncpg.create_pool(database='vdi', user='postgres')

    @asynccontextmanager
    @async_generator
    async def transaction(self) -> Connection:
        if self.pool is None:
            self.pool = await self.get_pool()
        async with self.pool.acquire() as c:
            async with c.transaction():
                await yield_(c)

    @asynccontextmanager
    @async_generator
    async def connect(self) -> Connection:
        if self.pool is None:
            self.pool = await self.get_pool()
        async with self.pool.acquire() as c:
            await yield_(c)



db = DbApp()

async def fetch(*query):
    async with db.connect() as conn:
        return await conn.fetch(*query)