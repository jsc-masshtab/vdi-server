from g_tasks import g, Task

import uuid
import json
import urllib
from tornado.httpclient import AsyncHTTPClient

from ..pool import pool

CONTROLLER_URL = 'http://192.168.20.120'

class Token(Task):
    creds = {
        'username': 'admin',
        'password': 'veil',
    }
    url = f'{CONTROLLER_URL}/auth/'

    async def run(self):
        http_client = AsyncHTTPClient()
        params = urllib.parse.urlencode(self.creds)
        response = await http_client.fetch(self.url, method='POST', body=params)
        response = json.loads(response.body)
        return response['token']


def get_vm_name():
    if 'vm_name' in g.values.get():
        return g.vm_name
    pool_config = pool.get_config()
    uid = str(uuid.uuid1()).split('-')[0]
    vm_name = f"{pool_config['vm_name_prefix']}-{uid}"
    g.set_attr('vm_name', vm_name)
    return vm_name

