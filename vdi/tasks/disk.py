
from g_tasks import g, Task

from .base import CONTROLLER_URL, Token

import json
from tornado.httpclient import AsyncHTTPClient


class DefaultDatapool(Task):

    url = '/api/data-pools/'

    async def run(self):
        token = await Token()
        url = f'{CONTROLLER_URL}{self.url}'
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
        params = g.request.query_params
        vm_type = params['vm_type']
        url = f"{CONTROLLER_URL}/api/library/?datapool_id={datapool['id']}"
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

    async def run(self):
        image_id = await Image()
        token = await Token()
        params = g.request.query_params
        vm_name = params['vm_name']
        http_client = AsyncHTTPClient()
        url = f'{CONTROLLER_URL}/api/library/{image_id}/import/?async=1'
        headers = {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }
        body = json.dumps({'verbose_name': vm_name})
        response = await http_client.fetch(url, method='POST', headers=headers, body=body)
        response = json.loads(response.body)
        entities = response['_task']['entities']
        for k, v in entities.items():
            if v == 'vdisk':
                return k
