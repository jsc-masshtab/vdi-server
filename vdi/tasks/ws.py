import json
from g_tasks import Task
from tornado.websocket import websocket_connect

from . import CONTROLLER_URL, Token

class WsConnection(Task):

    def send(self, msg):
        return (await self._conn.write_message(msg))

    def run(self):
        token = await Token()
        connect_url = f'ws://{CONTROLLER_URL}/ws/?token={token}'
        self._conn = await websocket_connect(connect_url)
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        msg = await self._conn.read_message()
        return json.loads(msg)