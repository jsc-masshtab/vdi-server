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


@pytest.mark.asyncio
async def test_copy(ctx):
    domain_id = '57014d61-38fe-4061-bc20-a9c5f09e8bd4'
    new_domain = await vm.CopyDomain(domain_id=domain_id)