
from typed_contextmanager import typed_contextmanager

import pytest

import asyncio

@typed_contextmanager
async def m() -> float:
    r = 0.5
    await asyncio.sleep(r)
    yield r

@m()
async def f(num: float):
    return num


@pytest.mark.asyncio
async def test():
    r = await f()
    assert r == 0.5