import json
from dataclasses import dataclass

from cached_property import cached_property as cached

from .base import UrlFetcher

from vdi.errors import FetchException, NotFound, SimpleError


@dataclass()
class EnableRemoteAccess(UrlFetcher):
    controller_ip: str
    domain_id: str

    method = 'POST'

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/remote-access/"

    async def body(self):
        return json.dumps({
            'remote_access': True
        })

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, FetchException) and exc_val.code == 404:
            raise NotFound("Виртуальная машина не найдена") from exc_val


POWER_STATES = ['unknown', 'power off', 'power on and suspended', 'power on']


@dataclass()
class PrepareVm(UrlFetcher):
    """
    Prepare for the first use: enable remote access & power on
    """
    controller_ip: str
    domain_id: str

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/"

    async def run(self):
        resp = await super().run()
        # assert resp['user_power_state'] == POWER_STATES.index('power off')
        await DoActionOnVm(controller_ip=self.controller_ip, domain_id=self.domain_id, action='start')
        # assert not resp['remote_access']
        info = await EnableRemoteAccess(controller_ip=self.controller_ip, domain_id=self.domain_id)
        return info

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, FetchException) and exc_val.code == 404:
            raise NotFound("Виртуальная машина не найдена") from exc_val


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


@dataclass()
class DoActionOnVm(UrlFetcher):
    controller_ip: str
    domain_id: str
    action: str
    body: str = ''

    method = 'POST'

    ACTIONS = [
        'start', 'suspend', 'reset', 'shutdown', 'resume'
    ]

    @cached
    def url(self):
        if self.action not in self.ACTIONS:
            raise SimpleError(f"Неизвестное действие: {self.action}")
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/{self.action}/"

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, FetchException) and exc_val.code == 404:
            raise NotFound("Виртуальная машина не найдена") from exc_val