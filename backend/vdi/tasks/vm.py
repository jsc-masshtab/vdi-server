import asyncio
import json
import uuid
#from dataclasses import dataclass

from cached_property import cached_property as cached

from vdi.errors import NotFound, FetchException, BadRequest
from .base import Token, UrlFetcher, DiscoverController, Task
from .client import HttpClient
from .ws import WsConnection


#@dataclass()
class CreateDomain(UrlFetcher):

    verbose_name = ''
    controller_ip = ''
    node_id = ''

    method = 'POST'

    def __init__(self, verbose_name: str, controller_ip: str, node_id: str):
        self.verbose_name = verbose_name
        self.controller_ip = controller_ip
        self.node_id = node_id

    @cached
    def url(self):
        return "http://{}//api/domains/".format(self.controller_ip)

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


#@dataclass()
class CopyDomain(UrlFetcher):

    cache_result = False # make a new domain every time this is called

    def __init__(self, controller_ip: str, domain_id: str, node_id: str, datapool_id:
                 str, verbose_name: str = None, name_template: str = None, is_thin: bool = True):
        self.controller_ip = controller_ip
        self.domain_id = domain_id
        self.node_id = node_id
        self.datapool_id = datapool_id
        self.verbose_name = verbose_name
        self.name_template = name_template

        self.is_thin = is_thin

    @cached
    def domain_name(self):
        if self.verbose_name:
            return self.verbose_name
        uid = str(uuid.uuid4())[:7]
        return "{}-{}".format(self.name_template, uid)

    method = 'POST'

    new_domain_id = None

    @cached
    def url(self):
        return "http://{}/api/domains/multi-create-domain/?async=1".format(self.controller_ip)

    async def body(self):
        params = {
            "verbose_name": self.domain_name,
            "node": self.node_id,
            "datapool": self.datapool_id,
            "parent": self.domain_id,
            "thin": self.is_thin
        }
        return json.dumps(params)

    async def run(self):
        loop = asyncio.get_event_loop()
        info_task = loop.create_task(self.fetch_template_info())
        #info_task = asyncio.create_task(self.fetch_template_info()) # python 3.7
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

    def on_fetch_failed(self, ex, code):
        if code == 400:
            raise BadRequest(ex) from ex

    def check_created(self, msg):
        obj = msg['object']
        if obj['parent'] != self.task_id:
            return

        def check_name(name):
            if name.startswith('Создание виртуальной машины'):
                return True
            if all(word in name.lower() for word in ['creating', 'virtual', 'machine']):
                return True
            return False

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
        url = "http://{}/api/domains/{}/".format(self.controller_ip, self.domain_id)
        headers = await self.headers()
        return await HttpClient().fetch(url, headers=headers)



#@dataclass()
class DropDomain(UrlFetcher):
    id = ''
    controller_ip = ''
    full = True

    method = 'POST'

    def __init__(self, id: str, controller_ip: str, full: bool = True):
        self.id = id
        self.controller_ip = controller_ip
        self.full = full

    @cached
    def url(self):
        return 'http://{}/api/domains/{}/remove/'.format(self.controller_ip, self.id)

    @cached
    def body(self):
        return json.dumps({'full': self.full})

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Виртуальная машина не найдена") from ex


#@dataclass()
class ListAllVms(Task):
    controller_ip = ''
    node_id = None

    def __init__(self, controller_ip: str, node_id: str = None):
        self.controller_ip = controller_ip
        self.node_id = node_id

    @cached
    def url(self):
        url = "http://{}/api/domains/".format(self.controller_ip)
        if self.node_id:
            url = '{}?node={}'.format(url, self.node_id)
        return url

    async def run(self):
        token = await Token(controller_ip=self.controller_ip)
        headers = {
            'Authorization': 'jwt {}'.format(token),
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


#@dataclass()
class GetDomainInfo(DiscoverController):
    """
    Tmp task
    Ensure vm is on a
    """
    domain_id = ''
    controller_ip = None

    def __init__(self, domain_id: str, controller_ip: str = None):
        self.domain_id = domain_id
        self.controller_ip = controller_ip

    @cached
    def url(self):
        return "http://{}/api/domains/{}/".format(self.controller_ip, self.domain_id)

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Виртуальная машина не найдена") from ex


#@dataclass()
class GetVdisks(DiscoverController):
    domain_id = ''
    controller_ip = None

    def __init__(self, domain_id: str, controller_ip: str = None):
        self.domain_id = domain_id
        self.controller_ip = controller_ip

    async def run(self):
        resp = await super().run()
        if not self.controller_ip:
            return resp
        return resp['results']


    @cached
    def url(self):
        return 'http://{}/api/vdisks/?domain={}'.format(self.controller_ip, self.domain_id)


