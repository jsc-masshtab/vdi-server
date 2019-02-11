from g_tasks import Task

import json
import urllib
from tornado.httpclient import AsyncHTTPClient

CONTROLLER_URL = 'http://192.168.20.120'

class Token(Task):
    creds = {
        'username': 'admin',
        'password': 'veil',
    }
    url = f'{CONTROLLER_URL}/auth/'

    async def run(self):
        http_client = AsyncHTTPClient()
        params = urllib.parse.urlencode(self.creds)
        response = await http_client.fetch(self.url, method='POST', body=params)
        response = json.loads(response.body)
        return response['token']
