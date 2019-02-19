import pytest
from g_tasks import g

from vdi.tasks import *


@pytest.fixture
def ctx():
    g.use_threadlocal()
    return g



@pytest.mark.asyncio
async def test(ctx):
    domain = await vm.SetupDomain()
