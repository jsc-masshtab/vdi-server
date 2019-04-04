
import pytest

from contextlib import suppress

from vdi.asyncio_utils import Awaitable

class Task(Awaitable):

    def __init__(self, *, artifact=None):
        self.artifact = artifact

    async def run(self):
        return self.artifact

@pytest.mark.asyncio
async def test():
    r = await Task(artifact=42)
    assert r == 42


class InheritTest(Awaitable):
    timeout = 0.5

    async def run(self):
        import asyncio
        await asyncio.sleep(1)
        return 1

@pytest.mark.asyncio
async def test_inherit():
    import time
    start = time.time()
    with suppress(Exception):
        await InheritTest()
    t = time.time() - start
    assert 0.4 < t < 0.6