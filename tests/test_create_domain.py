import pytest
from g_tasks import g

from vdi.tasks import disk, vm, CONTROLLER_URL


@pytest.fixture()
def request():
    class request:
        query_params = {
            'vm_type': 'disco',
            'vm_name': 'kvim2',
        }

    g.set_attr('request', request)
    return request

@pytest.fixture
def g_local():
    g.use_threadlocal()
    return g



@pytest.mark.asyncio
async def test_with_delays(request):
    domain = await vm.CreateDomain()
    checked = await vm.CheckDomain()
    assert domain['id'] == checked['id']
