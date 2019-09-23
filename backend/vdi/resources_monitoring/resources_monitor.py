import asyncio
import websockets
import json
from json import JSONDecodeError

from ..tasks.base import Token

from .resources_monitoring_data import ALLOWED_SUBSCRIPTIONS_LIST

class ResourcesMonitor:

    # ATTRIBUTES
    _websocket = None
    _running_flag = True
    _controller_ip = None

    _list_of_observers = []

    _resources_monitor_task = None

    # PUBLIC METHODS
    def start(self):
        loop = asyncio.get_event_loop()
        self._resources_monitor_task = loop.create_task(self._process_messages('192.168.7.250'))

    async def stop(self):
        # stop recv
        self._stop_running()
        # close connection
        if self._websocket:
            await self._websocket.close()
        # wait unlit task finished
        if self._resources_monitor_task:
            await self._resources_monitor_task

    def subscribe(self, observer):
        self._list_of_observers.append(observer)

    def unsubscribe(self, observer):
        self._list_of_observers.remove(observer)

    # PRIVATE METHODS
    async def _process_messages(self, controller_ip):
        self._controller_ip = controller_ip
        await self._connect()

        # receive messages
        while self._running_flag:
            await asyncio.sleep(0)
            try:
                message = await self._websocket.recv()
                await self._on_message_received(message)
            except websockets.ConnectionClosed:
                await self._on_connection_closed()
            except Exception:
                await self._on_error_occurred()

    async def _connect(self):
        try:
            # create ws connection
            token = await Token(controller_ip=self._controller_ip)
            connect_url = 'ws://{}/ws/?token={}'.format(self._controller_ip, token)
            self._websocket = await websockets.connect(connect_url)
        except:
            print('can not connect')
            return

        # subscribe to events on controller
        for subscription_name in ALLOWED_SUBSCRIPTIONS_LIST:
            await self._websocket.send('add /{}/'.format(subscription_name))

    def _stop_running(self):
        self._running_flag = False

    async def _on_message_received(self, message):
        try:
            json_data = json.loads(message)
            print('WS: ', json_data)
        except JSONDecodeError:
            return
        #  notify subscribed observers
        for observer in self._list_of_observers:
            observer.on_notified(json_data)

    async def _on_connection_closed(self):
        print('WS: cconnection closed')
        await self._try_to_recconect()

    async def _on_error_occurred(self):
        print('WS: An error occurred')
        if self._websocket:
            await self._websocket.close()
        await self._try_to_recconect()

    async def _try_to_recconect(self):
        # if _running_flag is raised then try to reconnect
        if self._running_flag:
            await self._connect()
            await asyncio.sleep(1)


veil_resources_monitor = ResourcesMonitor()