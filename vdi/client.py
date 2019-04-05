

from g_tasks import Task
from dataclasses import dataclass
import urllib
import json

from .tasks.client import HttpClient

from .tasks import CONTROLLER_IP, Token

@dataclass()
class PrepareVm(Task):
    """
    Prepare for use by the client: turn on & enable remote access
    """

    domain_id: str

    async def run(self):
        client = HttpClient()
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}'
        }
        body = urllib.parse.urlencode({
            'remote_access': True
        })
        url = f"http://{CONTROLLER_IP}/api/domains/{self.domain_id}/remote-access/"
        r = await client.fetch(url, method='POST', headers=headers, body=body)
        return {
            'host': CONTROLLER_IP,
            'port': r['remote_access_port'],
        }