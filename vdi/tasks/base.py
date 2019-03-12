from g_tasks import g, Task

import uuid
import json
import urllib
from tornado.httpclient import AsyncHTTPClient

from ..pool import Pool

from ..settings import settings
CONTROLLER_URL = settings['controller_url']

class Token(Task):
    creds = {
        'username': 'admin',
        'password': 'veil',
    }
    url = f'http://{CONTROLLER_URL}/auth/'

    async def run(self):
        http_client = AsyncHTTPClient()
        params = urllib.parse.urlencode(self.creds)
        response = await http_client.fetch(self.url, method='POST', body=params)
        response = json.loads(response.body)
        return response['token']

