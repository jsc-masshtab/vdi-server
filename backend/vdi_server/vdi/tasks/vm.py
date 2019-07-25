import asyncio
import json
import urllib
import uuid
from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async import Task, Awaitable, TaskTimeout

from . import disk
from .base import Token, UrlFetcher
from .client import HttpClient
from .ws import WsConnection

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
        token = await Token(controller_ip=self.controller_ip)
        headers = {
            'Authorization': f'jwt {token}'
        }
        ws = await WsConnection(controller_ip=self.controller_ip)
        await ws.send('add /tasks/')
        http_client = HttpClient()
        body = urllib.parse.urlencode(self.params)
        self.domain = await http_client.fetch(self.url, method='POST', headers=headers, body=body)
        await self.wait_message(ws)
        return self.domain


@dataclass()
class AttachVdisk(Task):
    controller_ip: str
    datapool_id: str
    domain_id: str
    vdisk: str

    method = 'POST'

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/attach-vdisk/"

    async def headers(self):
        token = await Token(controller_ip=self.controller_ip)
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
        ws = await WsConnection(controller_ip=self.controller_ip)
        await ws.send('add /tasks/')
        self.response = await HttpClient().fetch_using(self)
        await self.wait_message(ws)
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
        token = await Token(controller_ip=self.controller_ip)
        return {
            'Authorization': f'jwt {token}',
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
        name_template = params.pop('verbose_name')
        await CopyDomain(controller_ip=self.controller_ip, domain_id=self.domain_id, name_template=name_template,
                         **params)

# TODO API error

@dataclass()
class CopyDomain(UrlFetcher):

    controller_ip: str
    domain_id: str
    node_id: str
    datapool_id: str
    verbose_name: str = None
    name_template: str = None

    cache_result = False # make a new domain every time this is called

    @cached
    def domain_name(self):
        if self.verbose_name:
            return self.verbose_name
        uid = str(uuid.uuid4())[:7]
        return f"{self.name_template}-{uid}"


    method = 'POST'

    new_domain_id = None

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/domains/multi-create-domain/?async=1"

    async def body(self):
        params = {
            "verbose_name": self.domain_name,
            "node": self.node_id,
            "datapool": self.datapool_id,
            "parent": self.domain_id,
        }
        return json.dumps(params)

    async def run(self):
        info_task = asyncio.create_task(self.fetch_template_info())
        ws = await WsConnection(controller_ip=self.controller_ip)
        await ws.send('add /tasks/')
        resp = await super().run()
        self.task_id = resp['_task']['id']
        await self.wait_message(ws)
        info = await info_task
        return {
            'id': self.new_domain_id,
            'template': info,
            'verbose_name': self.domain_name,
        }

    def check_created(self, msg):
        obj = msg['object']
        if obj['parent'] == self.task_id:
            if obj['status'] == 'SUCCESS' and obj['name'].startswith('Создание виртуальной машины'):
                entities = {v: k for k, v in obj['entities'].items()}
                self.new_domain_id = entities['domain']

    def is_done(self, msg):
        if self.new_domain_id is None:
            self.check_created(msg)
            return

        if msg['id'] == self.task_id:
            obj = msg['object']
            if obj['status'] == 'SUCCESS':
                return True

    async def fetch_template_info(self):
        url = f"http://{self.controller_ip}/api/domains/{self.domain_id}/"
        headers = await self.headers()
        return await HttpClient().fetch(url, headers=headers)



@dataclass()
class DropDomain(Task):
    id: str
    controller_ip: str
    full: bool = True

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/domains/{self.id}/remove/'

    async def run(self):
        token = await Token(controller_ip=self.controller_ip)
        headers = {
            'Authorization': f'jwt {token}',
        }
        http_client = HttpClient()
        body = urllib.parse.urlencode({'full': self.full})

        await http_client.fetch(self.url, method='POST', headers=headers, body=body)


@dataclass()
class ListAllVms(Task):
    controller_ip: str

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/domains/"

    async def run(self):
        token = await Token(controller_ip=self.controller_ip)
        headers = {
            'Authorization': f'jwt {token}',
        }
        http_client = HttpClient()
        res = await http_client.fetch(self.url, headers=headers)
        return res['results']


class ListVms(ListAllVms):

    async def run(self):
        vms = await super().run()
        vms = [vm for vm in vms if not vm['template']]
        return vms



class ListTemplates(ListAllVms):

    async def run(self):
        vms = await super().run()
        vms = [vm for vm in vms if vm['template']]
        return vms


@dataclass()
class GetDomainInfo(UrlFetcher):
    """
    Tmp task
    Ensure vm is on a
    """

    domain_id: str
    controller_ip: str

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/"
