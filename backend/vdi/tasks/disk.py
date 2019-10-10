
import json
#from dataclasses import dataclass

from classy_async.classy_async import Task

from .base import Token
from .client import HttpClient
from .ws import WsConnection
from cached_property import cached_property as cached


class ImageNotFound(Exception):
    pass


#@dataclass()
class Image(Task):

    controller_ip = ''
    image_name = ''
    datapool_id = ''

    def __init__(self, controller_ip: str, image_name: str, datapool_id: str):
        self.controller_ip = controller_ip
        self.image_name = image_name
        self.datapool_id = datapool_id

    async def run(self):
        token = await Token(controller_ip=self.controller_ip)
        url = 'http://{}/api/library/?datapool_id={}'.format(self.controller_ip, self.datapool_id)
        http_client = HttpClient()
        headers = {
            'Authorization': 'jwt {}'.format(token)
        }
        response = await http_client.fetch(url, headers=headers)
        for file in response["results"]:
            if self.image_name in file["filename"].lower():
                return file["id"]
        else:
            raise ImageNotFound(self.image_name)


#@dataclass()
class ImportDisk(Task):
    """
    From a .qcow image
    """
    image_name = ''
    vm_name = ''
    controller_ip = ''
    datapool_id = ''

    def __init__(self, image_name: str, vm_name: str, controller_ip: str, datapool_id: str):
        self.image_name = image_name
        self.vm_name = vm_name
        self.controller_ip = controller_ip
        self.datapool_id = datapool_id

    def is_done(self, msg):
        return msg['object']['status'] == 'SUCCESS' and msg['id'] == self.task_obj['id']

    async def run(self):
        image_id = await Image(image_name=self.image_name,
                               datapool_id=self.datapool_id, controller_ip=self.controller_ip)
        token = await Token(controller_ip=self.controller_ip)
        ws = await WsConnection(controller_ip=self.controller_ip)
        await ws.send('add /tasks/')

        http_client = HttpClient()
        url = 'http://{}/api/library/{}/import/?async=1'.format(self.controller_ip, image_id)
        headers = {
            'Authorization': 'jwt {}'.format(token),
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
        await self.wait_message(ws)
        return disk_id


#@dataclass()
class CopyDisk(Task):

    controller_ip = ''
    datapool_id = ''
    vdisk = None
    verbose_name = ''

    method = 'POST'

    def __init__(self, controller_ip: str, datapool_id: str, vdisk: object, verbose_name: str):
        self.controller_ip = controller_ip
        self.datapool_id = datapool_id
        self.vdisk = vdisk
        self.verbose_name = verbose_name

    @cached
    def url(self):
        return 'http://{}/api/vdisks/{}/copy/?async=1'.format(self.controller_ip, self.vdisk)

    async def headers(self):
        token = await Token(controller_ip=self.controller_ip)
        return {
            'Authorization': 'jwt {}'.format(token),
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
        ws = await WsConnection(controller_ip=self.controller_ip)
        await ws.send('add /tasks/')
        response = await HttpClient().fetch_using(self)
        self.task_obj = response['_task']
        await self.wait_message(ws)
        return self.get_result()