from classy_async.classy_async import Task
#from contextlib import asynccontextmanager # python 3.7
from async_generator import async_generator, yield_, asynccontextmanager
import time


class RequestsLog(Task):
    async def run(self):
        return []

    @classmethod
    @asynccontextmanager
    @async_generator
    async def log(cls, **kwargs):
        log = await cls()
        start = time.time()
        try:
            await yield_(log)
        finally:
            took = time.time() - start
        log.append({'time': took, **kwargs})
