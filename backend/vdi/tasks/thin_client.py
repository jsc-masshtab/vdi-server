import json
#from dataclasses import dataclass

from cached_property import cached_property as cached

from .base import UrlFetcher

from vdi.errors import FetchException, NotFound, SimpleError


#@dataclass()
class EnableRemoteAccess(UrlFetcher):
    controller_ip = ''
    domain_id = ''

    method = 'POST'

    def __init__(self, controller_ip: str, domain_id: str):
        self.controller_ip = controller_ip
        self.domain_id = domain_id

    @cached
    def url(self):
        return "http://{}/api/domains/{}/remote-access/".format(self.controller_ip, self.domain_id)

    async def body(self):
        return json.dumps({
            'remote_access': True
        })

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Виртуальная машина не найдена") from ex


POWER_STATES = ['unknown', 'power off', 'power on and suspended', 'power on']


#@dataclass()
class PrepareVm(UrlFetcher):
    """
    Prepare for the first use: enable remote access & power on
    """
    controller_ip = ''
    domain_id = ''

    def __init__(self, controller_ip: str, domain_id: str):
        self.controller_ip = controller_ip
        self.domain_id = domain_id

    @cached
    def url(self):
        return "http://{}/api/domains/{}/".format(self.controller_ip, self.domain_id)

    async def run(self):
        resp = await super().run()
        # assert resp['user_power_state'] == POWER_STATES.index('power off')
        await DoActionOnVm(controller_ip=self.controller_ip, domain_id=self.domain_id, action='start')
        # assert not resp['remote_access']
        info = await EnableRemoteAccess(controller_ip=self.controller_ip, domain_id=self.domain_id)
        return info

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Виртуальная машина не найдена") from ex


#@dataclass()
#class PowerOn(UrlFetcher):
#    controller_ip: str
#    domain_id: str
#
#    method = 'POST'
#    body = ''
#
#    def url(self):
#        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/start/"


#@dataclass()
class DoActionOnVm(UrlFetcher):
    controller_ip = ''
    domain_id = ''
    action = ''
    body = ''

    method = 'POST'

    ACTIONS = [
        'start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot'
    ]

    def __init__(self, controller_ip: str, domain_id: str, action: str, body: str = ''):
        self.controller_ip = controller_ip
        self.domain_id = domain_id
        self.action = action
        self.body = body

    @cached
    def url(self):
        if self.action not in self.ACTIONS:
            raise SimpleError("Неизвестное действие: {}".format(self.action))
        return "http://{}/api/domains/{}/{}/".format(self.controller_ip, self.domain_id, self.action)

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise NotFound("Виртуальная машина не найдена") from ex