import json
from dataclasses import dataclass

from tornado.websocket import websocket_connect

from . import CONTROLLER_IP, Token
from classy_async import Awaitable
import asyncio

from classy_async import task


class WsConnection(Awaitable):

    timeout = 5 * 60

    async def send(self, msg):
        return (await self._conn.write_message(msg))

    async def run(self):
        token = await Token()
        connect_url = f'ws://{CONTROLLER_IP}/ws/?token={token}'
        self._conn = await websocket_connect(connect_url)
        return self

    def __aiter__(self):
        return self

    @task(timeout=timeout)
    async def wait_message(self, match_func):
        async for msg in self:
            try:
                matched = match_func(msg)
            except:
                matched = False
            if matched:
                self._conn.close()
                return msg


    async def __anext__(self):
        msg = await self._conn.read_message()
        return json.loads(msg)




