

import asyncio

import uuid
from g_tasks import Task

import urllib
import time

import json
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from dataclasses import dataclass

from .base import CONTROLLER_URL, Token
from . import disk
from .client import HttpClient
from .ws import WsConnection

from g_tasks import g

from ..asyncio_utils import sleep

from dataclasses import dataclass

from .disk import DefaultDatapool

import aiofiles

class AddNode(Task):

    url = f'http://{CONTROLLER_URL}/api/nodes/?async=1'
    method = 'POST'

    body = json.dumps({
        "management_ip": "192.168.20.121",
        "controller_ip": "192.168.20.120",
        "ssh_password": "bazalt",
        "verbose_name": "node1",
    })

    async def run(self):
        ws = await WsConnection()
        await ws.send('add /tasks/')
        token = await Token()
        headers = {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }
        response = await HttpClient().fetch_using(self, headers=headers)
        self.task_id = response['_task']['id']
        await ws.match_message(self.is_done)

    def is_done(self, msg):
        obj = msg['object']
        return obj['status'] == 'Выполнена' and obj['id'] == self.task_id


from cached_property import cached_property as cached

@dataclass()
class UploadDiskImage(Task):
    src: str = 'https://cloud-images.ubuntu.com/cosmic/current/cosmic-server-cloudimg-amd64.img'
    filename: str = 'ubuntu.qcow2'

    class End:
        pass

    @cached
    def queue(self):
        return asyncio.Queue()

    def on_chunk(self, chunk):
        self.queue.put_nowait(chunk)

    # async def write_file(self):
    #     async with aiofiles.open(self.out, 'wb') as f:
    #         while True:
    #             chunk = await self.queue.get()
    #             if chunk is self.End:
    #                 return
    #             await f.write(chunk)
    #             self.queue.task_done()

    async def body_producer(self, write):
        while True:
            chunk = await self.queue.get()
            if chunk is self.End:
                return
            write(chunk)
            self.queue.task_done()

    async def run(self):
        client = AsyncHTTPClient()
        token = await Token()
        datapool = await DefaultDatapool()
        headers = {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }
        url = f'http://{CONTROLLER_URL}/api/library/'
        body = json.dumps({
            'datapool': datapool['id'],
            'filename': self.filename,
        })
        res = await client.fetch(url, method='PUT', body=body, headers=headers)
        res = json.loads(res)
        self.upload_url = f"http://{CONTROLLER_URL}{res['upload_url']}"
        await self.do_upload()
        task = asyncio.create_task(self.write_file())
        await client.fetch(self.url, streaming_callback=self.on_chunk)
        self.queue.put_nowait(self.End)
        await task

    async def do_upload(self):
        client = AsyncHTTPClient()
        down_task = asyncio.create_task(
            client.fetch(self.src, streaming_callback=self.on_chunk)
        )
        client = AsyncHTTPClient()
        up_task = asyncio.create_task(
            client.fetch(self.upload_url, method="POST", body_producer=self.body_producer)
        )
        await down_task
        self.queue.put_nowait(self.End)
        await up_task
        #TODO: add ws