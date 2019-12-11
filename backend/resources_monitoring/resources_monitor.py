import asyncio
import time

from tornado.httpclient import HTTPClientError
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketClosedError
from tornado.websocket import websocket_connect

from common.veil_errors import HttpError
from controller.models import Controller
from controller_resources.veil_client import ResourcesHttpClient
from event.models import Event
from resources_monitoring.handlers import client_manager
from .resources_monitoring_data import CONTROLLER_SUBSCRIPTIONS_LIST, CONTROLLERS_SUBSCRIPTION


class ResourcesMonitor:
    """
    monitoring of controller events
    """
    RECONNECT_TIMEOUT = 5

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
        # controller check
        self._controller_online_task = IOLoop.instance().add_timeout(time.time(), self._controller_online_checking)
        # ws data
        self._resources_monitor_task = IOLoop.instance().add_timeout(time.time(), self._processing_ws_messages)

    async def stop(self):
        self._running_flag = False
        await self._close_connection()
        # cancel tasks
        IOLoop.instance().remove_timeout(self._resources_monitor_task)
        IOLoop.instance().remove_timeout(self._controller_online_task)

    def get_controller_ip(self):
        return self._controller_ip

    # PRIVATE METHODS
    async def _controller_online_checking(self):
        """
        Check if controller online
        :return:
        """
        resources_http_client = await ResourcesHttpClient.create(self._controller_ip)

        response_dict = {'ip': self._controller_ip, 'msg_type': 'data', 'event': 'UPDATED',
                         'resource': CONTROLLERS_SUBSCRIPTION}
        while self._running_flag:
            await asyncio.sleep(2)  # check every 2 seconds
            try:
                # if controller is online then there wil not be any exception
                await resources_http_client.check_controller()
            except (HTTPClientError, HttpError, OSError):
                # notify only if controller was online before (data changed)
                if self._is_online:
                    response_dict['status'] = 'OFFLINE'
                    await client_manager.send_message(response_dict)
                self._is_online = False
            else:
                # notify only if controller was offline before (data changed)
                if not self._is_online:
                    response_dict['status'] = 'ONLINE'
                    await client_manager.send_message(response_dict)
                self._is_online = True

    async def _processing_ws_messages(self):
        """
        Listen for data from controller
        :return:
        """
        while self._running_flag:
            is_connected = await self._connect()
            print(__class__.__name__, ' is_connected', is_connected)
            # reconnect if not connected
            if not is_connected:
                await asyncio.sleep(self.RECONNECT_TIMEOUT)
                continue

            # receive messages
            while self._running_flag:
                msg = await self._ws_connection.read_message()
                if msg is None:  # according to doc it means that connection closed
                    break
                elif 'token error' in msg:
                    await Controller.invalidate_auth(self._controller_ip)
                else:
                    await self._on_message_received(msg)

            await asyncio.sleep(self.RECONNECT_TIMEOUT)

    async def _connect(self):
        # get token
        try:
            token = await Controller.get_token(self._controller_ip)
        except Exception as E:
            print(E)
            return False

        # create ws connection
        try:
            connect_url = 'ws://{}/ws/?token={}'.format(self._controller_ip, token)
            self._ws_connection = await websocket_connect(connect_url)
        except ConnectionRefusedError:
            msg = '{cls}: an not connect to {ip}'.format(
                cls=__class__.__name__,
                ip=self._controller_ip)
            await Event.create_error(msg)
            return False

        # subscribe to events on controller
        try:
            for subscription_name in CONTROLLER_SUBSCRIPTIONS_LIST:
                await self._ws_connection.write_message('add {}'.format(subscription_name))
        except WebSocketClosedError:
            return False

        return True

    async def _on_message_received(self, message):
        print(__class__.__name__, 'msg received from {}:'.format(self._controller_ip), message)
        await client_manager.send_message(message)

    async def _close_connection(self):
        if self._ws_connection:
            print(__class__.__name__, 'Closing ws connection', self._controller_ip)
            self._ws_connection.close()
