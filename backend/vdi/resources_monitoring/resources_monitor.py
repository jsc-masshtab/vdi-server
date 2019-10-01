import asyncio
import websockets
import json
from json import JSONDecodeError

from ..tasks.base import Token

from .resources_monitoring_data import ALLOWED_SUBSCRIPTIONS_LIST

from vdi.utils import cancel_async_task


class ResourcesMonitor:
    """
    monitoring of controller
    """
    def __init__(self):
        self._websocket = None
        self._running_flag = True
        self._controller_ip = None
        self._list_of_observers = []

        self._controller_online_task = None
        self._resources_monitor_task = None

    # PUBLIC METHODS
    def start(self, controller_ip):
        self._controller_ip = controller_ip
        self._running_flag = True
        # ws data
        loop = asyncio.get_event_loop()
        self._resources_monitor_task = loop.create_task(self._process_messages())

    async def stop(self):
        self._running_flag = False
        await self._close_connection()
        # wait unlit task finished
        await cancel_async_task(self._resources_monitor_task)

    def subscribe(self, observer):
        self._list_of_observers.append(observer)

    def unsubscribe(self, observer):
        self._list_of_observers.remove(observer)

    def unsubscribe_all(self):
        self._list_of_observers.clear()

    def get_controller_ip(self):
        return self._controller_ip

    # PRIVATE METHODS
    async def _process_messages(self):
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
            self._websocket = await websockets.connect(connect_url) #

            # subscribe to events on controller
            for subscription_name in ALLOWED_SUBSCRIPTIONS_LIST:
                await self._websocket.send('add {}'.format(subscription_name))
        except:
            print(__class__.__name__, ' can not connect')
            return

    async def _on_message_received(self, message):
        try:
            json_data = json.loads(message)
            print(__class__.__name__, json_data)
        except JSONDecodeError:
            return
        #  notify subscribed observers
        try:
            resource_str = json_data['resource']
        except KeyError:
            return
        #  print('resource_str', resource_str)
        for observer in self._list_of_observers:
            if resource_str in observer.get_subscriptions():
                observer.on_notified(json_data)

    async def _on_connection_closed(self):
        print(__class__.__name__, 'connection closed')
        await self._try_to_recconect()

    async def _on_error_occurred(self):
        #print(__class__.__name__, 'An error occurred')
        await self._close_connection()
        await self._try_to_recconect()

    async def _try_to_recconect(self):
        # if _running_flag is raised then try to reconnect
        if self._running_flag:
            await self._connect()
            await asyncio.sleep(5)

    async def _close_connection(self):
        try:
            if self._websocket:
                print(__class__.__name__, 'before close conn')
                await self._websocket.close()
                await self._websocket.wait_closed()
                print(__class__.__name__, 'after close conn')
        except websockets.exceptions.ConnectionClosed:
            pass


