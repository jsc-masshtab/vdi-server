import json
import uuid
#from dataclasses import dataclass
from classy_async.classy_async import Task

from .base import Token
from .client import HttpClient
from .ws import WsConnection

from vdi.settings import settings
from vdi.tasks import resources


from cached_property import cached_property as cached

from pathlib import Path

#@dataclass()
class AddNode(Task):

    controller_ip = ''
    management_ip = ''
    method = 'POST'

    def __ini__(self, controller_ip: str, management_ip: str):
        self.controller_ip = controller_ip
        self.management_ip = management_ip

    @cached
    def url(self):
        return 'http://{}/api/nodes/?async=1'.format(self.controller_ip)

    @cached
    def body(self):
        return {
            "management_ip": self.management_ip,
            "controller_ip": self.controller_ip,
            "ssh_password": "bazalt",
            "verbose_name": "node1",
        }

    async def check_present(self):
        client = HttpClient()
        url = "http://{}/api/nodes/".format(self.controller_ip)
        token = await Token(controller_ip=self.controller_ip)
        headers = {
            'Authorization': 'jwt {}'.format(token),
            'Content-Type': 'application/json',
        }
        res = await client.fetch(url, headers=headers)
        for node in res['results']:
            if node['management_ip'] == self.body['management_ip']:
                return node


    async def run(self):
        node = await self.check_present()
        if node:
            return node['id']
        ws = await WsConnection(controller_ip=self.controller_ip)
        await ws.send('add /tasks/')
        token = await Token(controller_ip=self.controller_ip)
        headers = {
            'Authorization': 'jwt {}'.format(token),
            'Content-Type': 'application/json',
        }
        response = await HttpClient().fetch_using(self, headers=headers, body=json.dumps(self.body))
        self.task_id = response['_task']['id']
        await self.wait_message(ws)
        [node_id] = response['_task']['nodes_list']
        return node_id

    def is_done(self, msg):
        obj = msg['object']
        return obj['status'] == 'SUCCESS' and obj['id'] == self.task_id


#@dataclass()
class DownloadImage(Task):
    target = ''
    src = 'https://cloud-images.ubuntu.com/cosmic/current/cosmic-server-cloudimg-amd64.img'

    timeout = 5 * 60

    def __init__(self, target: str,
                 src: str = 'https://cloud-images.ubuntu.com/cosmic/current/cosmic-server-cloudimg-amd64.img'):
        self.target = target
        self.src = src

    async def run(self):
        target = Path(self.target)
        if target.exists():
            return {
                'used_existing': True
            }
        client = HttpClient()

        with target.open('wb') as f:
            def on_chunk(c):
                f.write(c)
            await client.fetch(self.src, streaming_callback=on_chunk, request_timeout=24 * 3600)
            return {
                'used_existing': False
            }

#@dataclass()
class UploadImage(Task):
    filename = ''
    datapool_id = ''
    controller_ip = ''

    def __init__(self, filename: str, datapool_id: str, controller_ip: str):
        self.filename = filename
        self.datapool_id = datapool_id
        self.controller_ip = controller_ip

    async def check_present(self):
        token = await Token(controller_ip=self.controller_ip)
        url = "http://{}/api/library/?datapool_id={}".format(self.controller_ip, self.datapool_id)
        http_client = HttpClient()
        headers = {
            'Authorization': 'jwt {}'.format(token)
        }
        response = await http_client.fetch(url, headers=headers)
        for file in response["results"]:
            if file["filename"] == self.filename:
                return True

    async def get_upload_url(self):
        client = HttpClient()
        token = await Token(controller_ip=self.controller_ip)
        headers = {
            'Authorization': 'jwt {}'.format(token),
            'Content-Type': 'application/json',
        }
        url = 'http://{}/api/library/'.format(self.controller_ip)
        body = json.dumps({
            'datapool': self.datapool_id,
            'filename': self.filename,
        })
        res = await client.fetch(url, method='PUT', body=body, headers=headers)
        return "http://{}{}".format(self.controller_ip, res['upload_url'])

    @cached
    def boundary(self):
        return uuid.uuid4().hex

    async def body_producer(self, write):
        filename_bytes = self.filename.encode()
        boundary_bytes = self.boundary.encode()
        buf = (
                (b"--%s\r\n" % boundary_bytes)
                + (
                    b'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
                    % (filename_bytes, filename_bytes)
                )
                + b"Content-Type: application/octet-stream\r\n"
                + b"\r\n"
        )
        await write(buf)
        with open(self.filename, "rb") as f:
            while True:
                # 16k at a time.
                chunk = f.read(16 * 1024)
                if not chunk:
                    break
                await write(chunk)

        await write(b"\r\n")
        await write(b"--%s--\r\n" % (boundary_bytes,))


    async def run(self):
        present = await self.check_present()
        if present:
            return
        upload_url = await self.get_upload_url()
        ws = await WsConnection(controller_ip=self.controller_ip)
        await ws.send("add /tasks/")
        await ws.send("add /events/")

        client = HttpClient()
        token = await Token(controller_ip=self.controller_ip)
        headers = {
            "Content-Type": "multipart/form-data; boundary=%s" % self.boundary,
            'Authorization': 'jwt {}'.format(token),
        }
        return await client.fetch(upload_url, method="POST", headers=headers, body_producer=self.body_producer,
                                 request_timeout=24 * 3600)


