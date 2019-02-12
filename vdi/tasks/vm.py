import asyncio
from g_tasks import g, Task

import urllib
import time

import json
from tornado.httpclient import AsyncHTTPClient

from .base import CONTROLLER_URL, Token
from . import disk
from .client import HttpClient


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
        return json.loads(response.body)


class CheckDomain(Task):

    url = f"{CONTROLLER_URL}/api/domains"

    delta_t = 0.1
    timeout = 5

    async def headers(self):
        token = await Token()
        return {
            'Authorization': f'jwt {token}'
        }

    async def run(self):
        vm_name = g.request.query_params['vm_name']
        await CreateDomain()
        t = start = time.time()
        while t - start < self.timeout:
            r = await HttpClient().fetch_using(self)
            for domain in r['results']:
                if domain['verbose_name'] == vm_name:
                    return domain
            print('.', end='')
            if time.time() - t < self.delta_t:
                await asyncio.sleep(self.delta_t)
            t = time.time()
            return r


class AttachVdisk(Task):
    method = 'POST'

    async def url(self):
        domain = await CreateDomain()  # ['id']
        return f"{CONTROLLER_URL}/api/domains/{domain['id']}/attach-vdisk/"

    async def body(self):
        vdisk = await disk.ImportDisk()
        datapool = await disk.DefaultDatapool()
        params = {
            "type_storage": "local",
            "storage": datapool['id'],
            "driver_cache": "none",
            "target_bus": "virtio",
            "vdisk": vdisk
        }
        return json.dumps(params)

    async def run(self):
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}'
        }
        response = HttpClient().fetch_using(self)
        return response


class SetupDomain(Task):

    async def run(self):
        domain = await CreateDomain()
        await CheckDomain()
        await AttachVdisk()
        return domain