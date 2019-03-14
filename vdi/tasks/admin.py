

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

MAX_BODY_SIZE = 10 * 1024 * 1024 * 1024

AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient",
                          max_body_size=MAX_BODY_SIZE,
                          )

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
#
# @dataclass()
# class UploadDiskImage(Task):
#     # src: str = 'https://cloud-images.ubuntu.com/cosmic/current/cosmic-server-cloudimg-amd64.img'
#     src: str = 'https://cloud-images.ubuntu.com/cosmic/current/cosmic-server-cloudimg-amd64.img'
#     filename: str = 'ubuntu.qcow2'
#
#     class END:
#         pass
#
#     @cached
#     def queue(self):
#         return asyncio.Queue()
#
#     def on_chunk(self, chunk):
#         self.queue.put_nowait(chunk)
#
#     # async def write_file(self):
#     #     async with aiofiles.open(self.out, 'wb') as f:
#     #         while True:
#     #             chunk = await self.queue.get()
#     #             if chunk is self.END:
#     #                 return
#     #             await f.write(chunk)
#     #             self.queue.task_done()
#
#     # async def body_producer(self, write):
#     #     while True:
#     #         chunk = await self.queue.get()
#     #         if chunk is self.END:
#     #             return
#     #         write(chunk)
#     #         self.queue.task_done()
#
#     @cached
#     def boundary(self):
#         return uuid.uuid4().hex
#
#     async def body_producer(self, write):
#         filename_bytes = self.filename.encode()
#         boundary_bytes = self.boundary.encode()
#         buf = (
#                 (b"--%s\r\n" % boundary_bytes)
#                 + (
#                     b'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
#                     % (filename_bytes, filename_bytes)
#                 )
#                 + b"Content-Type: application/octet-stream\r\n"
#                 + b"\r\n"
#         )
#         await write(buf)
#         while True:
#             chunk = await self.queue.get()
#             if chunk is self.END:
#                 break
#             await write(chunk)
#             self.queue.task_done()
#
#         await write(b"\r\n")
#         await write(b"--%s--\r\n" % (boundary_bytes,))
#
#     async def get_upload_url(self):
#         client = AsyncHTTPClient()
#         token = await Token()
#         datapool = await DefaultDatapool()
#         headers = {
#             'Authorization': f'jwt {token}',
#             'Content-Type': 'application/json',
#         }
#         url = f'http://{CONTROLLER_URL}/api/library/'
#         body = json.dumps({
#             'datapool': datapool['id'],
#             'filename': self.filename,
#         })
#         res = await client.fetch(url, method='PUT', body=body, headers=headers)
#         res = json.loads(res.body)
#         return f"http://{CONTROLLER_URL}{res['upload_url']}"
#
#     async def run(self):
#         self.upload_url = await self.get_upload_url()
#         ws = await WsConnection()
#         await ws.send('add /tasks/')
#
#         async def down():
#             client = AsyncHTTPClient(max_body_size=10 * 1024 * 1024 * 1024)
#             res = await client.fetch(self.src, streaming_callback=self.on_chunk)
#             return res
#
#         async def up():
#             client = AsyncHTTPClient()
#             res = await client.fetch(self.upload_url, method="POST", body_producer=self.body_producer)
#             return res
#
#         down_task = asyncio.create_task(down())
#         up_task = asyncio.create_task(up())
#         await down_task
#         self.queue.put_nowait(self.END)
#         await up_task
#         async for msg in ws:
#             print('ws', msg)
#
#
#
# import requests
# import uuid
#
# @dataclass()
# class UploadFile(Task):
#     filename: str
#     src: str = '/home/pwtail/Downloads/get-pip.qcow2'
#
#     async def get_upload_url(self):
#         client = AsyncHTTPClient()
#         token = await Token()
#         datapool = await DefaultDatapool()
#         headers = {
#             'Authorization': f'jwt {token}',
#             'Content-Type': 'application/json',
#         }
#         url = f'http://{CONTROLLER_URL}/api/library/'
#         body = json.dumps({
#             'datapool': datapool['id'],
#             'filename': self.filename,
#         })
#         res = await client.fetch(url, method='PUT', body=body, headers=headers)
#         res = json.loads(res.body)
#         return f"http://{CONTROLLER_URL}{res['upload_url']}"
#
#     # async def body_producer(self, write):
#     #     async with aiofiles.open(self.src, 'rb') as f:
#     #         chunk = await f.read(4096)
#     #         await write(chunk)
#     #
#     # @cached
#     # def body(self):
#     #     with open(self.src, 'rb') as f:
#     #         return f.read()
#
#     async def multipart_producer(self, write):
#         filename = self.filename
#         boundary = self.boundary
#         boundary_bytes = boundary.encode()
#
#         filename_bytes = filename.encode()
#         mtype = "application/octet-stream"
#         buf = (
#                 (b"--%s\r\n" % boundary_bytes)
#                 + (
#                         b'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
#                         % (filename_bytes, filename_bytes)
#                 )
#                 + (b"Content-Type: %s\r\n" % mtype.encode())
#                 + b"\r\n"
#         )
#         await write(buf)
#         with open(self.src, "rb") as f:
#             while True:
#                 # 16k at a time.
#                 chunk = f.read(16 * 1024)
#                 if not chunk:
#                     break
#                 await write(chunk)
#
#             await write(b"\r\n")
#
#         await write(b"--%s--\r\n" % (boundary_bytes,))
#
#     @cached
#     def boundary(self):
#         return uuid.uuid4().hex
#
#     async def run(self):
#         client = AsyncHTTPClient()
#         upload_url = await self.get_upload_url()
#         token = await Token()
#         headers = {
#             "Content-Type": "multipart/form-data; boundary=%s" % self.boundary,
#             'Authorization': f'jwt {token}',
#         }
#         response = await client.fetch(
#             upload_url,
#             method="POST",
#             headers=headers,
#             body_producer=self.multipart_producer,
#         )
#
#         return response


from pathlib import Path

@dataclass()
class DownloadImage(Task):
    target: str
    src: str = 'https://cloud-images.ubuntu.com/cosmic/current/cosmic-server-cloudimg-amd64.img'

    async def run(self):
        target = Path(self.target)
        if target.exists():
            return
        client = AsyncHTTPClient()

        with target.open('wb') as f:
            def on_chunk(c):
                f.write(c)
            res = await client.fetch(self.src, streaming_callback=on_chunk, request_timeout=24 * 3600)
        return res


@dataclass()
class UploadImage(Task):
    filename: str

    async def get_upload_url(self):
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
        res = json.loads(res.body)
        return f"http://{CONTROLLER_URL}{res['upload_url']}"

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
        upload_url = await self.get_upload_url()
        ws = await WsConnection()
        await ws.send(f"add /tasks/")
        await ws.send(f"add /events/")

        client = AsyncHTTPClient()
        token = await Token()
        headers = {
            "Content-Type": "multipart/form-data; boundary=%s" % self.boundary,
            'Authorization': f'jwt {token}',
        }
        res = await client.fetch(upload_url, method="POST", headers=headers, body_producer=self.body_producer,
                                 request_timeout=24 * 3600)

        return json.loads(res.body)
