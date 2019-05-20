

from classy_async import Task
from dataclasses import dataclass
import urllib
import json

from .client import HttpClient
from . import CONTROLLER_IP, Token
from .base import UrlFetcher

@dataclass()
class EnableRemoteAccess(UrlFetcher):
    controller_ip: str
    domain_id: str

    method = 'POST'

    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/remote-access/"

    async def body(self):
        return json.dumps({
            'remote_access': True
        })

POWER_STATES = ['unknown', 'power off', 'power on and suspended', 'power on']


@dataclass()
class PrepareVm(UrlFetcher):
    """
    Prepare for the first use: enable remote access & power on
    """
    controller_ip: str
    domain_id: str

    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/"

    async def run(self):
        resp = await super().run()
        assert resp['user_power_state'] == POWER_STATES.index('power off')
        await PowerOn(controller_ip=self.controller_ip, domain_id=self.domain_id)
        assert not resp['remote_access']
        info = await EnableRemoteAccess(controller_ip=self.controller_ip, domain_id=self.domain_id)
        return info



@dataclass()
class PowerOn(UrlFetcher):
    controller_ip: str
    domain_id: str

    method = 'POST'
    body = ''

    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/start/"


@dataclass()
class GetDomainInfo(UrlFetcher):
    """
    Tmp task
    Ensure vm is on a
    """

    domain_id: str
    controller_ip: str

    def url(self):
        return f"http://{self.controller_ip}/api/domains/{self.domain_id}/"
