import json
from g_tasks import Task
from tornado.websocket import websocket_connect

from . import CONTROLLER_IP, Token
from vdi.asyncio_utils import Awaitable
import asyncio

from vdi.asyncio_utils import Wait


class WsTimeout(Exception):
    pass


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

    async def wait_message(self, match_func, timeout=None):
        if timeout is None:
            timeout = self.timeout
        sleep_task = self.make_sleep_task(timeout)
        ws_task = asyncio.create_task(self._match_message(match_func))
        async for result, task in Wait(sleep_task, ws_task).items():
            if hasattr(task, 'i_am_timeout'):
                ws_task.cancel()
                raise WsTimeout
            sleep_task.cancel()
            return result


    async def _match_message(self, match_func):
        async for msg in self:
            try:
                if match_func(msg):
                    return msg
            except:
                pass

    def make_sleep_task(self, timeout):
        async def sleep_co():
            await asyncio.sleep(timeout)
        t = asyncio.create_task(sleep_co())
        t.i_am_timeout = True
        return t

    async def __anext__(self):
        msg = await self._conn.read_message()
        return json.loads(msg)

