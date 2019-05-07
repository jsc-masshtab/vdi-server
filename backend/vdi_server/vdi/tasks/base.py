import urllib

from cached_property import cached_property as cached
from classy_async import Task

from vdi.settings import settings
from vdi.tasks.client import HttpClient

CONTROLLER_IP = settings['controller_ip']

class Token(Task):
    creds = {
        'username': 'admin',
        'password': 'veil',
    }
    url = f'http://{CONTROLLER_IP}/auth/'

    async def run(self):

        http_client = HttpClient()
        params = urllib.parse.urlencode(self.creds)
        response = await http_client.fetch(self.url, method='POST', body=params)
        return response['token']


class UrlFetcher(Task):

    async def headers(self):
        return {
            'Authorization': f'jwt {await Token()}',
            'Content-Type': 'application/json',
        }

    @cached
    def client(self):
        return HttpClient()

    def __repr__(self):
        return repr(self.client)

    async def run(self):
        return await self.client.fetch_using(self)

