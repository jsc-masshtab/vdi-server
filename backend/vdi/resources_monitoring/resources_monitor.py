import asyncio
import websockets
import json
from json import JSONDecodeError

from ..tasks.base import Token

from .resources_monitoring_data import ALLOWED_SUBSCRIPTIONS_LIST, CONTROLLERS_SUBSCRIPTION

from vdi.utils import cancel_async_task

from ..tasks.resources import (
  CheckController
)

class ResourcesMonitor:
    """
    monitoring of controller
    """
    def __init__(self):
        self._websocket = None
        self._running_flag = True
        self._controller_ip = None
        self._list_of_observers = []

        self._is_online = False

        self._controller_online_task = None
        self._resources_monitor_task = None

    # PUBLIC METHODS
    def start(self, controller_ip):
        self._controller_ip = controller_ip
        self._running_flag = True
        loop = asyncio.get_event_loop()
        # controller check
        self._controller_online_task = loop.create_task(self._controller_online_checking())
        # ws data
        self._resources_monitor_task = loop.create_task(self._process_ws_messages())

    async def stop(self):
        self._running_flag = False
        await self._close_connection()
        # wait unlit task finished
        await cancel_async_task(self._resources_monitor_task)
        await cancel_async_task(self._controller_online_task)

    def subscribe(self, observer):
        self._list_of_observers.append(observer)

    def unsubscribe(self, observer):
        self._list_of_observers.remove(observer)

    def unsubscribe_all(self):
        self._list_of_observers.clear()

    def get_controller_ip(self):
        return self._controller_ip

    # PRIVATE METHODS
    async def _controller_online_checking(self):
        """
        Check if controller online
        :return:
        """
        response_dict = {'ip': self._controller_ip, 'msg_type': 'data', 'event': 'UPDATED',
                         'resource': CONTROLLERS_SUBSCRIPTION}
        while self._running_flag:
            await asyncio.sleep(2) # check every 2 seconds
            try:
                # if controller is online then there wil not be any exception
                #print('before check self._controller_ip', self._controller_ip)
                await CheckController(controller_ip=self._controller_ip)
                #print('after check self._controller_ip')
            except:
                # notify only if controller was online before (data changed)
                if self._is_online:
                    response_dict['status'] = 'OFFLINE'
                    json_data = json.dumps(response_dict)
                    self._notify_observers(CONTROLLERS_SUBSCRIPTION, json_data)
                    print('notify controller offline')
                self._is_online = False
            else:
                # notify only if controller was offline before (data changed)
                if not self._is_online:
                    response_dict['status'] = 'ONLINE'
                    json_data = json.dumps(response_dict)
                    self._notify_observers(CONTROLLERS_SUBSCRIPTION, json_data)
                    print('notify controller online')
                self._is_online = True

    async def _process_ws_messages(self):
        """
        Listen for data from controller
        :return:
        """
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
                if not (subscription_name == CONTROLLERS_SUBSCRIPTION):
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
        self._notify_observers(resource_str, json_data)

    async def _on_connection_closed(self):
        print(__class__.__name__, 'connection closed')
        await self._try_to_recconect()

    def _notify_observers(self, sub_source, json_data):
        for observer in self._list_of_observers:
            if sub_source in observer.get_subscriptions():
                observer.on_notified(json_data)

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
                #await self._websocket.wait_closed()
                print(__class__.__name__, 'after close conn')
        except websockets.exceptions.ConnectionClosed:
            pass
