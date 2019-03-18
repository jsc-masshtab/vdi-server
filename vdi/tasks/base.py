from g_tasks import g, Task

import uuid
import json
import urllib

from ..pool import Pool

from vdi.tasks.client import HttpClient

from ..settings import settings
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
        response = json.loads(response.body)
        return response['token']

