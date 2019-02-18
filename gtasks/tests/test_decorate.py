import pytest

from g_tasks import task, g as the_g

class Obj:

    @task
    async def my_method(self):
        return 1


@pytest.fixture()
def g():
    the_g.init()

@pytest.mark.asyncio
async def test(g):
    o = Obj()
    r = await o.my_method()
    assert r == 1

spoiled = []

@task
async def spoil():
    spoiled.append(1)


@pytest.mark.asyncio
async def test_lazy(g):
    t = spoil()
    assert not spoiled
    await t
    assert spoiled