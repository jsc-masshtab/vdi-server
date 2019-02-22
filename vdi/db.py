from cached_property import cached_property as cached

import asyncpg
from functools import wraps

from contextlib import contextmanager

class DbApp:

    @cached
    def pool(self):
        p = await asyncpg.create_pool(database='postgres',
                                      user='postgres')
        return p

    @contextmanager
    def transaction_conn(self):
        async with self.pool.acquire() as c:
            async with c.transaction():
                yield c

db = DbApp()