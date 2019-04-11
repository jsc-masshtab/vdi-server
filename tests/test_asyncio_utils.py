
import pytest
import time
import asyncio

from vdi.asyncio_utils import wait

li = []

async def task(i):
    await asyncio.sleep(i)
    li.append(i)
    return i

@pytest.mark.asyncio
async def test_wait():
    count = 5

    tasks = [
        task(i) for i in range(count)
    ]
    t = time.time()
    i = 0
    async for r in wait(*tasks):
        assert i == r
        i += 1

    t = time.time() - t

    assert count - 2 < t < count