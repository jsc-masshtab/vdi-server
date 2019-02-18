
from g_tasks import Task, task

from .base import CONTROLLER_URL, Token, get_vm_name
from .ws import WsConnection

from ..pool import pool

import json
from tornado.httpclient import AsyncHTTPClient


class DefaultDatapool(Task):

    url = '/api/data-pools/'

    async def run(self):
        token = await Token()
        url = f'http://{CONTROLLER_URL}{self.url}'
        headers = {
            'Authorization': f'jwt {token}'
        }
        http_client = AsyncHTTPClient()
        response = await http_client.fetch(url, headers=headers)
        response = json.loads(response.body)
        for rec in response['results']:
            if 'default datapool' in rec['verbose_name'].lower():
                return rec


class Image(Task):

    async def run(self):
        token = await Token()
        datapool = await DefaultDatapool()
        pool_config = pool.get_config()
        vm_type = pool_config['vm_type']
        url = f"http://{CONTROLLER_URL}/api/library/?datapool_id={datapool['id']}"
        http_client = AsyncHTTPClient()
        headers = {
            'Authorization': f'jwt {token}'
        }
        response = await http_client.fetch(url, headers=headers)
        response = json.loads(response.body)
        for file in response["results"]:
            if vm_type in file["filename"].lower():
                return file["id"]


class ImportDisk(Task):

    def is_done(self, msg):
        return msg['object']['status'] == 'Выполнена' and msg['id'] == self.task['id']

    async def run(self):
        image_id = await Image()
        token = await Token()
        ws = await WsConnection()
        await ws.send('add /tasks/')
        vm_name = get_vm_name()

        http_client = AsyncHTTPClient()
        url = f'http://{CONTROLLER_URL}/api/library/{image_id}/import/?async=1'
        headers = {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }
        body = json.dumps({'verbose_name': vm_name})
        response = await http_client.fetch(url, method='POST', headers=headers, body=body)
        response = json.loads(response.body)
        self.task = response['_task']
        # ? self.response
        entities = self.task['entities']
        for k, v in entities.items():
            if v == 'vdisk':
                disk_id = k
                break
        await ws.match_message(self.is_done)
        return disk_id
