import json
from g_tasks import Task
from tornado.websocket import websocket_connect

from . import CONTROLLER_URL, Token
from vdi.asyncio_utils import Awaitable

class WsConnection(Awaitable):

    async def send(self, msg):
        return (await self._conn.write_message(msg))

    async def run(self):
        token = await Token()
        connect_url = f'ws://{CONTROLLER_URL}/ws/?token={token}'
        self._conn = await websocket_connect(connect_url)
        return self

    def __aiter__(self):
        return self

    async def match_message(self, match_func):
        async for msg in self:
            try:
                if match_func(msg):
                    return msg
            except:
                pass

    async def __anext__(self):
        msg = await self._conn.read_message()
        return json.loads(msg)

