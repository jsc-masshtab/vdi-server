import asyncio
import json
from json import JSONDecodeError
from abc import ABC, abstractmethod

from tornado.httpclient import HTTPClientError
from tornado.websocket import websocket_connect

from ..tasks.base import Token

from .resources_monitoring_data import CONTROLLER_SUBSCRIPTIONS_LIST, CONTROLLERS_SUBSCRIPTION, VDI_TASKS_SUBSCRIPTION

from vdi.utils import cancel_async_task
from vdi.errors import NotFound

from ..tasks.resources import (
  CheckController
)


class AbstractMonitor(ABC):

    def __init__(self):
        self._list_of_observers = []

    # PUBLIC METHODS
    def subscribe(self, observer):
        if observer not in self._list_of_observers:
            self._list_of_observers.append(observer)

    def unsubscribe(self, observer):
        if observer in self._list_of_observers:
            self._list_of_observers.remove(observer)

    def unsubscribe_all(self):
        self._list_of_observers.clear()

    def notify_observers(self, sub_source, json_data):
        for observer in self._list_of_observers:
            if sub_source in observer.get_subscriptions():
                observer.on_notified(json_data)


class ResourcesMonitor(AbstractMonitor):
    """
    monitoring of controller events
    """
    def __init__(self):
        super().__init__()
        self._ws_connection = None
        self._running_flag = True
        self._controller_ip = None

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
        self._resources_monitor_task = loop.create_task(self._processing_ws_messages())

    async def stop(self):
        self._running_flag = False
        await self._close_connection()
        # wait unlit task finished
        await cancel_async_task(self._resources_monitor_task)
        await cancel_async_task(self._controller_online_task)

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
            await asyncio.sleep(2)  # check every 2 seconds
            try:
                # if controller is online then there wil not be any exception
                #  print('before check self._controller_ip', self._controller_ip)
                await CheckController(controller_ip=self._controller_ip)
                #  print('after check self._controller_ip')
            except (HTTPClientError, OSError, NotFound):
                # notify only if controller was online before (data changed)
                if self._is_online:
                    response_dict['status'] = 'OFFLINE'
                    json_data = json.dumps(response_dict)
                    self.notify_observers(CONTROLLERS_SUBSCRIPTION, json_data)
                    print('notify controller offline ', self._controller_ip)
                self._is_online = False
            else:
                # notify only if controller was offline before (data changed)
                if not self._is_online:
                    response_dict['status'] = 'ONLINE'
                    json_data = json.dumps(response_dict)
                    self.notify_observers(CONTROLLERS_SUBSCRIPTION, json_data)
                    print('notify controller online ', self._controller_ip)
                self._is_online = True

    async def _processing_ws_messages(self):
        """
        Listen for data from controller
        :return:
        """
        await self._connect()

        # receive messages
        while self._running_flag:
            msg = await self._ws_connection.read_message()
            if msg is None:  # according to doc it means that connection closed
                await self._on_connection_closed()
            await self._on_message_received(msg)

    async def _connect(self):
        # get token
        try:
            token = await Token(controller_ip=self._controller_ip)
        except Exception:
            return
        # create ws connection
        try:
            connect_url = 'ws://{}/ws/?token={}'.format(self._controller_ip, token)
            self._ws_connection = await websocket_connect(connect_url)

            # subscribe to events on controller
            for subscription_name in CONTROLLER_SUBSCRIPTIONS_LIST:
                await self._ws_connection.write_message('add {}'.format(subscription_name))
        except ConnectionRefusedError:
            print(__class__.__name__, ' can not connect to', self._controller_ip)
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
        self.notify_observers(resource_str, json_data)

    async def _on_connection_closed(self):
        print(__class__.__name__, 'connection closed ', self._controller_ip, self._ws_connection.open)
        await self._try_to_reconnect()

    async def _try_to_reconnect(self):
        # if _running_flag is raised then try to reconnect
        if self._running_flag:
            await self._connect()
            RECONNECT_TIMEOUT = 5
            await asyncio.sleep(RECONNECT_TIMEOUT)

    async def _close_connection(self):
        if self._ws_connection:
            print(__class__.__name__, 'Closing ws connection', self._controller_ip)
            self._ws_connection.close()


class InternalMonitor(AbstractMonitor):
    """
    monitoring of internal VDI events (pool progress creation, result of pool creation...)
    """
    def __init__(self):
        super().__init__()

    # PUBLIC METHODS
    def signal_event(self, json_data):
        self.notify_observers(VDI_TASKS_SUBSCRIPTION, json_data)
