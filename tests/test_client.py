import pytest

from g_tasks import g, Task

from vdi.tasks import disk, vm, CONTROLLER_IP
from vdi.tasks.client import HttpClient





@pytest.mark.asyncio
async def test_attrs():

    class ListDomains(Task):
        url = f"http://{CONTROLLER_IP}/api/domains"

        async def headers(self):
            token = await disk.Token()
            return {
                'Authorization': f'jwt {token}'
            }

        async def run(self):
            client = HttpClient()
            r = await client.fetch_using(self)
            return r


    r = await ListDomains()
    assert 'results' in r


@pytest.mark.asyncio
async def test_http_request():

    class ListDomains(Task):
        url = f"http://{CONTROLLER_IP}/api/domains"

        async def http_request(self):
            token = await disk.Token()
            headers = {
                'Authorization': f'jwt {token}'
            }
            return locals()

        async def run(self):
            client = HttpClient()
            r = await client.fetch_using(self)
            return r

    r = await ListDomains()
    assert 'results' in r