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

from vdi.errors import NotFound, FetchException, BadRequest


@dataclass()
class CreateDomain(UrlFetcher):

    verbose_name: str
    controller_ip: str
    node_id: str

    method = 'POST'

    @cached
    def url(self):
        return f"http://{self.controller_ip}//api/domains/"

    async def body(self):
        params = {
            "verbose_name": self.verbose_name,
            "node": self.node_id,
            "cpu_count": 1,
            "cpu_priority": 10,
            "memory_count": 128,
            "os_type": "Other",
            "boot_type": "LegacyMBR"
   # "sound" : {"model": "ich6", "codec": "micro"},
   # "video": {"heads": 1, "type": "cirrus", "vram": 16384}
        }
        return json.dumps(params)


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

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, FetchException) and exc_val.http_error.code == 400:
            raise BadRequest(exc_val) from exc_val

    def check_created(self, msg):
        obj = msg['object']
        if obj['parent'] != self.task_id:
            return

        def check_name(name):
            if name.startswith('Создание виртуальной машины'):
                return True
            if all(word in name.lower() for word in ['creating', 'virtual', 'machine']):
                return True

        if obj['status'] == 'SUCCESS' and check_name(obj['name']):
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
class DropDomain(UrlFetcher):
    id: str
    controller_ip: str
    full: bool = True

    method = 'POST'

    @cached
    def url(self):
        return f'http://{self.controller_ip}/api/domains/{self.id}/remove/'

    @cached
    def body(self):
        return json.dumps({'full': self.full})

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, FetchException) and exc_val.code == 404:
            raise NotFound("Виртуальная машина не найдена") from exc_val



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

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, FetchException) and exc_val.code == 404:
            raise NotFound("Виртуальная машина не найдена") from exc_val
