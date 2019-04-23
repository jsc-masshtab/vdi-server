import json
import uuid
from dataclasses import dataclass
from classy_async import Task

from .base import CONTROLLER_IP, Token
from .client import HttpClient
from .ws import WsConnection


from cached_property import cached_property as cached

from pathlib import Path

@dataclass()
class AddNode(Task):

    management_ip: str = '192.168.20.121'
    url = f'http://{CONTROLLER_IP}/api/nodes/?async=1'
    method = 'POST'

    body = {
        "management_ip": management_ip,
        "controller_ip": "192.168.20.120",
        "ssh_password": "bazalt",
        "verbose_name": "node1",
    }

    async def check_present(self):
        client = HttpClient()
        url = f"http://{CONTROLLER_IP}/api/nodes/"
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }
        res = await client.fetch(url, headers=headers)
        for node in res['results']:
            if node['management_ip'] == self.body['management_ip']:
                return True
        return False


    async def run(self):
        present = await self.check_present()
        if present:
            return
        ws = await WsConnection()
        await ws.send('add /tasks/')
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }
        response = await HttpClient().fetch_using(self, headers=headers, body=json.dumps(self.body))
        self.task_id = response['_task']['id']
        await ws.wait_message(self.is_done)

    def is_done(self, msg):
        obj = msg['object']
        return obj['status'] == 'SUCCESS' and obj['id'] == self.task_id


@dataclass()
class DownloadImage(Task):
    target: str
    src: str = 'https://cloud-images.ubuntu.com/cosmic/current/cosmic-server-cloudimg-amd64.img'

    timeout = 5 * 60

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

@dataclass()
class UploadImage(Task):
    filename: str

    async def check_present(self):
        token = await Token()
        datapool = await DefaultDatapool()
        url = f"http://{CONTROLLER_IP}/api/library/?datapool_id={datapool['id']}"
        http_client = HttpClient()
        headers = {
            'Authorization': f'jwt {token}'
        }
        response = await http_client.fetch(url, headers=headers)
        for file in response["results"]:
            if file["filename"] == self.filename:
                return True

    async def get_upload_url(self):
        client = HttpClient()
        token = await Token()
        datapool = await DefaultDatapool()
        headers = {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }
        url = f'http://{CONTROLLER_IP}/api/library/'
        body = json.dumps({
            'datapool': datapool['id'],
            'filename': self.filename,
        })
        res = await client.fetch(url, method='PUT', body=body, headers=headers)
        return f"http://{CONTROLLER_IP}{res['upload_url']}"

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
        ws = await WsConnection()
        await ws.send(f"add /tasks/")
        await ws.send(f"add /events/")

        client = HttpClient()
        token = await Token()
        headers = {
            "Content-Type": "multipart/form-data; boundary=%s" % self.boundary,
            'Authorization': f'jwt {token}',
        }
        return await client.fetch(upload_url, method="POST", headers=headers, body_producer=self.body_producer,
                                 request_timeout=24 * 3600)
