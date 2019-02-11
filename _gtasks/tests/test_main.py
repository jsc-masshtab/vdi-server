
from g_tasks import g, task
from vdi.asyncio_utils import Wait

import asyncio

import pytest

@task
async def b():
    await asyncio.sleep(1)
    g.tasks['message'].set_result('how are you?')
    return 1

@task
async def c():
    await asyncio.sleep(1)
    return 1

@task
async def d():
    await asyncio.sleep(1)
    return 1

@task
async def e():
    await asyncio.sleep(1)
    msg = await g.tasks['message']
    return f"{g.request['params']['greeting']} {msg}"


async def a():
    await asyncio.sleep(1)
    async for _ in Wait(b, c, d):
        pass
    return (await e)


# async def a1():
#     li = []
#     print('yay: ', end='')
#     async for r in Wait(b, c, d):
#         print(r, end=' ')
#     print()

@pytest.mark.asyncio
async def test_1():
    request = {'params': {'greeting': 'Bo!'}}
    g.set_attr('request', request)
    import time
    start = time.time()
    # asyncio.create_task(a1())
    v = await a()
    print(f'time: {time.time() - start}')
    await asyncio.sleep(2)
    print(v)