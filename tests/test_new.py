


import pytest

@pytest.fixture()
async def fixt():
    import asyncio
    await asyncio.sleep(0.5)
    return 1


@pytest.mark.asyncio
async def test(fixt):
    # fixt = await fixt
    assert fixt == 2
