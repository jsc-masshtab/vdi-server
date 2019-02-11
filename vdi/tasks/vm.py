from g_tasks import g, Task

import urllib

import json
from tornado.httpclient import AsyncHTTPClient

from .base import CONTROLLER_URL, Token
from . import disk


class Node(Task):

    async def run(self):
        datapool = await disk.DefaultDatapool()
        nodes = datapool['nodes_connected']
        if len(nodes) == 1:
            [node] = nodes
            if node['connection_status'] == 'SUCCESS':
                return node['id']


class CreateDomain(Task):

    url = f'{CONTROLLER_URL}/api/domains/'

    async def params(self):
        node_id = await Node()
        return {
            'cpu_count': 1,
            'cpu_priority': "10",
            'memory_count': 1024,
            'node': node_id,
            'os_type': "Other",
            'sound': {'model': "ich6", 'codec': "micro"},
            'verbose_name': g.request.query_params['vm_name'],
            'video': {'type': "cirrus", 'vram': "16384", 'heads': "1"},
        }

    async def run(self):
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}'
        }
        http_client = AsyncHTTPClient()
        params = await self.params()
        body = urllib.parse.urlencode(params)
        response = await http_client.fetch(self.url, method='POST', headers=headers, body=body)
        return response