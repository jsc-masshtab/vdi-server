import asyncio

import uuid
from g_tasks import Task

import urllib
import time

import json
from tornado.httpclient import AsyncHTTPClient

from dataclasses import dataclass

from .base import CONTROLLER_URL, Token
from . import disk
from .client import HttpClient
from .ws import WsConnection

from g_tasks import g

from ..asyncio_utils import sleep


class Node(Task):

    async def run(self):
        datapool = await disk.DefaultDatapool()
        nodes = datapool['nodes_connected']
        if len(nodes) == 1:
            [node] = nodes
            if node['connection_status'] == 'SUCCESS':
                return node['id']


@dataclass()
class CreateDomain(Task):

    vm_name: str

    url = f'http://{CONTROLLER_URL}/api/domains/'

    async def params(self):
        node_id = await Node()
        return {
            'cpu_count': 1,
            'cpu_priority': "10",
            'memory_count': 1024,
            'node': node_id,
            'os_type': "Other",
            'sound': {'model': "ich6", 'codec': "micro"},
            'verbose_name': self.vm_name,
            'video': {'type': "cirrus", 'vram': "16384", 'heads': "1"},
        }

    async def check_done(self, task_id):
        async for msg in self.ws:
            try:
                if msg['object']['status'] == 'Выполнена' and msg['id'] == task_id:
                    return True
            except KeyError:
                pass

    def is_done(self, msg):
        obj = msg['object']
        if not obj['status'] == 'Выполнена':
            return
        for id, e in obj['entities'].items():
            if e == 'domain':
                return id == self.domain['id']

    async def run(self):
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}'
        }
        ws = await WsConnection()
        await ws.send('add /tasks/')
        http_client = AsyncHTTPClient()
        params = await self.params()
        body = urllib.parse.urlencode(params)
        response = await http_client.fetch(self.url, method='POST', headers=headers, body=body)
        self.domain = json.loads(response.body)
        await ws.match_message(self.is_done)
        return self.domain


@dataclass()
class AttachVdisk(Task):
    method = 'POST'

    domain: object
    vdisk: str

    async def url(self):
        return f"http://{CONTROLLER_URL}/api/domains/{self.domain['id']}/attach-vdisk/"

    async def body(self):
        datapool = await disk.DefaultDatapool()
        params = {
            "type_storage": "local",
            "storage": datapool['id'],
            "driver_cache": "none",
            "target_bus": "virtio",
            "vdisk": self.vdisk,
        }
        return urllib.parse.urlencode(params)

    def is_done(self, msg):
        obj = msg['object']
        if obj['status'] != 'Выполнена':
            return
        for e_id, e_type in obj['entities'].items():
            if e_type == 'vdisk' and self.vdisk != e_id:
                return
            if e_type == 'domain' and self.domain['id'] != e_id:
                return
        return True

    async def run(self):
        ws = await WsConnection()
        await ws.send('add /tasks/')
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}'
        }
        self.response = await HttpClient().fetch_using(self, headers=headers)
        await ws.match_message(self.is_done)
        return True


@dataclass()
class SetupDomain(Task):

    image_name: str
    vm_name: str = None

    async def run(self):
        if self.vm_name is None:
            uid = str(uuid.uuid1()).split('-')[0]
            self.vm_name = f'{self.image_name}-{uid}'
        vdisk = await disk.ImportDisk(image_name=self.image_name, vm_name=self.vm_name)
        domain = await CreateDomain(vm_name=self.vm_name)
        await AttachVdisk(vdisk=vdisk, domain=domain)
        return domain


@dataclass()
class CopyDomain(Task):

    domain_id: str
    vm_name: str


    async def list_vdisks(self):
        url = f'http://{CONTROLLER_URL}/api/vdisks/?domain={self.domain_id}'
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}'
        }
        response = await HttpClient().fetch_using(headers=headers, url=url)
        vdisks = []
        for d in response['results']:
            if d['status'] != 'ACTIVE':
                continue
            vdisks.append(d['id'])
        return vdisks

    async def run(self):
        # this is a root task
        g.init()
        [vdisk0] = await self.list_vdisks()
        domain = await CreateDomain(vm_name=self.vm_name)
        vdisk = await disk.CopyDisk(vdisk=vdisk0, verbose_name=domain['verbose_name'])
        await AttachVdisk(domain=domain, vdisk=vdisk)
        return domain