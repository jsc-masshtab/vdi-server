import urllib

from cached_property import cached_property as cached
from classy_async import Task

from vdi.settings import settings
from vdi.tasks.client import HttpClient

from dataclasses import dataclass

CONTROLLER_IP = settings['controller_ip']

from vdi.settings import settings

@dataclass()
class Token(Task):
    controller_ip: str

    creds = settings.credentials

    @cached
    def url(self):
        return f'http://{self.controller_ip}/auth/'

    async def run(self):

        http_client = HttpClient()
        params = urllib.parse.urlencode(self.creds)
        response = await http_client.fetch(self.url, method='POST', body=params)
        return response['token']


@dataclass()
class UrlFetcher(Task):
    controller_ip: str

    async def headers(self):
        token = await Token(controller_ip=self.controller_ip)
        return {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }

    @cached
    def client(self):
        return HttpClient()

    def __repr__(self):
        return repr(self.client)

    async def run(self):
        return await self.client.fetch_using(self)

