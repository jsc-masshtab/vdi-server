
from classy_async import Task, task

from .base import CONTROLLER_IP, Token
from .ws import WsConnection
from .client import HttpClient

from ..pool import Pool

import json

from dataclasses import dataclass


class DefaultDatapool(Task):
    "Only for debug"

    url = '/api/data-pools/'

    async def run(self):
        token = await Token()
        url = f'http://{CONTROLLER_IP}{self.url}'
        headers = {
            'Authorization': f'jwt {token}'
        }
        http_client = HttpClient()
        response = await http_client.fetch(url, headers=headers)
        for rec in response['results']:
            if 'default' in rec['verbose_name'].lower():
                return rec
            if 'базовый' in rec['verbose_name'].lower():
                return rec


class ImageNotFound(Exception):
    pass


@dataclass()
class Image(Task):

    image_name: str

    async def run(self):
        token = await Token()
        datapool = await DefaultDatapool()
        url = f"http://{CONTROLLER_IP}/api/library/?datapool_id={datapool['id']}"
        http_client = HttpClient()
        headers = {
            'Authorization': f'jwt {token}'
        }
        response = await http_client.fetch(url, headers=headers)
        for file in response["results"]:
            if self.image_name in file["filename"].lower():
                return file["id"]
        else:
            raise ImageNotFound(self.image_name)


@dataclass()
class ImportDisk(Task):
    """
    From a .qcow image
    """

    image_name: str
    vm_name: str

    def is_done(self, msg):
        return msg['object']['status'] == 'SUCCESS' and msg['id'] == self.task_obj['id']

    async def run(self):
        image_id = await Image(image_name=self.image_name)
        token = await Token()
        ws = await WsConnection()
        await ws.send('add /tasks/')

        http_client = HttpClient()
        url = f'http://{CONTROLLER_IP}/api/library/{image_id}/import/?async=1'
        headers = {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }
        body = json.dumps({'verbose_name': self.vm_name})
        response = await http_client.fetch(url, method='POST', headers=headers, body=body)
        self.task_obj = response['_task']
        # ? self.response
        entities = self.task_obj['entities']
        for k, v in entities.items():
            if v == 'vdisk':
                disk_id = k
                break
        await ws.wait_message(self.is_done)
        return disk_id


@dataclass()
class CopyDisk(Task):

    controller_ip: str
    datapool_id: str
    vdisk: object
    verbose_name: str

    method = 'POST'

    def url(self):
        return f'http://{self.controller_ip}/api/vdisks/{self.vdisk}/copy/?async=1'

    async def headers(self):
        token = await Token()
        return {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }

    def body(self):
        dic = {
            'verbose_name': self.verbose_name,
            'datapool': self.datapool_id,
        }
        return json.dumps(dic)


    def is_done(self, msg):
        obj = msg['object']
        return obj['id'] == self.task_obj['id'] and obj['status'] == 'SUCCESS'

    def get_result(self):
        """
        The copied disk
        """
        for e_id, e_type in self.task_obj['entities'].items():
            if e_type == 'vdisk' and e_id != self.vdisk:
                return e_id

    async def run(self):
        ws = await WsConnection()
        await ws.send('add /tasks/')
        response = await HttpClient().fetch_using(self)
        self.task_obj = response['_task']
        await ws.wait_message(self.is_done)
        return self.get_result()