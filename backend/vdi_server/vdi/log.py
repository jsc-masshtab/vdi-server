from classy_async import Task
from contextlib import asynccontextmanager
import time


class RequestsLog(Task):
    async def run(self):
        return []

    @classmethod
    @asynccontextmanager
    async def log(cls, **kwargs):
        log = await cls()
        start = time.time()
        try:
            yield log
        finally:
            took = time.time() - start
        log.append({'time': took, **kwargs})
