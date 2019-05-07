import json
import urllib
import uuid
from dataclasses import dataclass

from cached_property import cached_property as cached

from classy_async import Task, Awaitable

from . import disk
from .base import CONTROLLER_IP, Token, UrlFetcher
from .client import HttpClient
from .ws import WsConnection

from vdi.settings import settings
from vdi.tasks import resources

from classy_async import wait


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
    controller_ip: str
    node_id: str

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/domains/'

    @cached
    def params(self):
        return {
            'cpu_count': 1,
            'cpu_priority': "10",
            'memory_count': 1024,
            'node': self.node_id,
            'os_type': "Other",
            'sound': {'model': "ich6", 'codec': "micro"},
            'verbose_name': self.vm_name,
            'video': {'type': "cirrus", 'vram': "16384", 'heads': "1"},
        }

    def is_done(self, msg):
        obj = msg['object']
        if not obj['status'] == 'SUCCESS':
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
        http_client = HttpClient()
        body = urllib.parse.urlencode(self.params)
        self.domain = await http_client.fetch(self.url, method='POST', headers=headers, body=body)
        await ws.wait_message(self.is_done)
        return self.domain


@dataclass()
class AttachVdisk(Task):
    controller_ip: str
    datapool_id: str
    domain_id: str
    vdisk: str

    method = 'POST'


    async def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/attach-vdisk/"

    async def headers(self):
        token = await Token()
        return {
            'Authorization': f'jwt {token}'
        }

    def body(self):
        params = {
            "type_storage": "local",
            "storage": self.datapool_id,
            "driver_cache": "none",
            "target_bus": "virtio",
            "vdisk": self.vdisk,
        }
        return urllib.parse.urlencode(params)

    def is_done(self, msg):
        obj = msg['object']
        if obj['status'] != 'SUCCESS':
            return
        for e_id, e_type in obj['entities'].items():
            if e_type == 'vdisk' and self.vdisk != e_id:
                return
            if e_type == 'domain' and self.domain_id != e_id:
                return
        return True

    async def run(self):
        ws = await WsConnection()
        await ws.send('add /tasks/')
        self.response = await HttpClient().fetch_using(self)
        await ws.wait_message(self.is_done)
        return True


@dataclass()
class SetupDomain(Task):

    image_name: str
    controller_ip: str
    node_id: str
    datapool_id: str

    @cached
    def vm_name(self):
        uid = str(uuid.uuid1()).split('-')[0]
        return f'{self.image_name}-{uid}'

    async def run(self):
        vdisk = await disk.ImportDisk(image_name=self.image_name, vm_name=self.vm_name,
                                      controller_ip=self.controller_ip, datapool_id=self.datapool_id)
        domain = await CreateDomain(vm_name=self.vm_name,
                                    controller_ip=self.controller_ip, node_id=self.node_id)
        await AttachVdisk(vdisk=vdisk, domain_id=domain['id'],
                          datapool_id=self.datapool_id, controller_ip=self.controller_ip)
        return domain


@dataclass()
class CopyDomainDebug(Awaitable):

    controller_ip: str
    domain_id: str

    @cached
    def client(self):
        return HttpClient()

    async def headers(self):
        return {
            'Authorization': f'jwt {await Token()}',
        }

    async def get_datapool_id(self):
        url = f"http://{self.controller_ip}/api/vdisks/?domain={self.domain_id}"
        r = await self.client.fetch_using(self, url=url)
        datapool_id = []
        for r in r['results']:
            if r['domain']['id'] == self.domain_id:
                datapool_id.append(r['datapool']['id'])
        assert datapool_id
        try:
            [datapool_id] = datapool_id
            return datapool_id
        except ValueError:
            return tuple(datapool_id)

    async def get_params(self):
        url = f"http://{self.controller_ip}/api/domains/{self.domain_id}/"
        r = await self.client.fetch_using(self, url=url)
        node_id = r['node']['id']
        verbose_name = r['verbose_name']
        datapool_id = await self.get_datapool_id()
        return {
            'node_id': node_id,
            'verbose_name': verbose_name,
            'datapool_id': datapool_id,
        }

    async def run(self):
        params = await self.get_params()
        uid = str(uuid.uuid4())[:3]
        verbose_name = f"{params.pop('verbose_name')}-{uid}"
        await CopyDomain(controller_ip=self.controller_ip, domain_id=self.domain_id, verbose_name=verbose_name,
                         **params)


@dataclass()
class CopyDomain(UrlFetcher):

    verbose_name: str
    controller_ip: str
    domain_id: str
    node_id: str
    datapool_id: str

    method = 'POST'

    new_domain_id = None

    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/clone/?async=1"

    def check_created(self, msg):
        obj = msg['object']
        if obj['parent'] == self.task_id:
            if obj['status'] == 'SUCCESS' and obj['name'].startswith('Создание виртуальной машины'):
                entities = {v: k for k, v in obj['entities'].items()}
                self.new_domain_id = entities['domain']

    def is_done(self, msg):
        if self.new_domain_id is None:
            self.check_created(msg)

        if msg['id'] == self.task_id:
            obj = msg['object']
            if obj['status'] == 'SUCCESS':
                return True

    async def run(self):
        ws = await WsConnection()
        await ws.send('add /tasks/')
        resp = await super().run()
        self.task_id = resp['_task']['id']
        await ws.wait_message(self.is_done)
        return {
            'new_domain_id': self.new_domain_id,
        }

    async def body(self):
        params = {
            "verbose_name": self.verbose_name,
            "node": self.node_id,
            "datapool": self.datapool_id,
        }
        return json.dumps(params)



@dataclass()
class DropDomain(Task):
    id: str

    @cached
    def url(self):
        return f'http://{CONTROLLER_IP}/api/domains/{self.id}/remove/'

    async def run(self):
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}',
        }
        http_client = HttpClient()
        await http_client.fetch(self.url, method='POST', headers=headers, body=b'')


@dataclass()
class ListVms(Task):
    controller_ip: str

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/domains/"

    async def run(self):
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}',
        }
        http_client = HttpClient()
        res = await http_client.fetch(self.url, headers=headers)
        return res['results']


class DropAllDomains(Task):

    async def run(self):
        vms = await ListVms()

        tasks = [
            DropDomain(id=vm['id']) for vm in vms
        ]
        # async for _ in wait(*tasks):
        #     pass
        for t in tasks:
            await t
