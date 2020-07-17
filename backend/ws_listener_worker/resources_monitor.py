# -*- coding: utf-8 -*-
import asyncio
import json

from front_ws_api.subscription_sources import SubscriptionCmd

from tornado.httpclient import HTTPClientError
from tornado.websocket import WebSocketClosedError
from tornado.websocket import WebSocketError
from tornado.websocket import websocket_connect

from common.veil_errors import HttpError
from controller.models import Controller
from controller_resources.veil_client import ResourcesHttpClient

from front_ws_api.subscription_sources import CONTROLLER_SUBSCRIPTIONS_LIST, CONTROLLERS_SUBSCRIPTION

from common.utils import cancel_async_task

from redis_broker import REDIS_CLIENT, WS_MONITOR_CHANNEL_OUT

from languages import lang_init
from journal.journal import Log


_ = lang_init()


class ResourcesMonitor():
    """
    monitoring of controller events
    """
    RECONNECT_TIMEOUT = 8

    def __init__(self):
        super().__init__()
        self._ws_connection = None
        self._running_flag = True
        self._controller_id = None
        self._is_online = False

        self._controller_online_task = None
        self._resources_monitor_task = None

    # PUBLIC METHODS
    def start(self, controller_id):

        self._controller_id = controller_id
        self._running_flag = True

        native_loop = asyncio.get_event_loop()
        # controller check
        self._controller_online_task = native_loop.create_task(self._controller_online_checking())
        # ws data
        self._resources_monitor_task = native_loop.create_task(self._processing_ws_messages())

    async def stop(self):

        self._running_flag = False
        await self._close_connection()
        # cancel tasks
        await cancel_async_task(self._resources_monitor_task)
        await cancel_async_task(self._controller_online_task)

    def get_controller_id(self):
        return self._controller_id

    # PRIVATE METHODS
    async def _controller_online_checking(self):
        """
        Check if controller online
        :return:
        """
        controller_address = await Controller.get_controller_address_by_id(self._controller_id)
        response = {'id': str(self._controller_id), 'msg_type': 'data', 'event': 'UPDATED',
                    'resource': CONTROLLERS_SUBSCRIPTION}

        is_first_check = True

        while self._running_flag:

            await asyncio.sleep(4)
            try:
                # if controller is online then there wil not be any exception
                resources_http_client = await ResourcesHttpClient.create(controller_address)
                await resources_http_client.check_controller()
            except (HTTPClientError, HttpError, Exception):
                # notify if controller was online before (data changed)
                if self._is_online or is_first_check:
                    response['status'] = 'OFFLINE'
                    REDIS_CLIENT.publish(WS_MONITOR_CHANNEL_OUT, json.dumps(response))

                    # await Controller.deactivate(self._controller_id)  # Под вопросом нужно ли менять какие-либо
                    # данные в бд либо мы лишь наблюдаем.
                    self._is_online = False
            else:
                # notify if controller was offline before (data changed)
                if not self._is_online or is_first_check:
                    response['status'] = 'ONLINE'
                    REDIS_CLIENT.publish(WS_MONITOR_CHANNEL_OUT, json.dumps(response))

                    # await Controller.activate(self._controller_id)  # Под вопросом нужно ли менять какие-либо данные
                    self._is_online = True

            is_first_check = False

    async def _processing_ws_messages(self):
        """
        Listen for data from controller
        :return:
        """
        while self._running_flag:
            is_connected = await self._connect()
            Log.debug(_('{} is connected: {}').format(__class__.__name__, is_connected))  # noqa
            # reconnect if not connected
            if not is_connected:
                await asyncio.sleep(self.RECONNECT_TIMEOUT)
                continue

            # receive messages
            while self._running_flag:
                msg = await self._ws_connection.read_message()
                if msg is None:  # according to doc it means that connection closed
                    Log.debug('{} Probably connection is closed by server.').format(__class__.__name__)  # noqa
                    break
                elif 'token error' in msg:
                    Log.debug('{} token error. Closing connection.').format(__class__.__name__)  # noqa
                    # Если токен эррор, то закрываем соединение и и переходим к попыткам коннекта (начало первого while)
                    await self._close_connection()
                    # await Controller.invalidate_auth(self._controller_id)
                    break
                else:
                    await self._on_message_received(msg)

            await asyncio.sleep(self.RECONNECT_TIMEOUT)

    async def _connect(self):
        controller = await Controller.get(self._controller_id)

        # check if controller active
        if not controller.active:
            return False

        # get token
        try:
            token = await Controller.get_token(controller.address)
        except Exception as E:
            await Log.error(str(E))
            return False

        # create ws connection
        try:
            connect_url = 'ws://{}/ws/?token={}'.format(controller.address, token)
            # Log.debug('ws connection url is {}'.format(connect_url))
            self._ws_connection = await websocket_connect(connect_url)
        except (ConnectionRefusedError, WebSocketError):
            msg = _('{cls}: can not connect to {ip}').format(
                cls=__class__.__name__, # noqa
                ip=controller.address)
            await Log.error(msg)
            return False

        # subscribe to events on controller
        try:
            for subscription_name in CONTROLLER_SUBSCRIPTIONS_LIST:
                await self._ws_connection.write_message(
                    SubscriptionCmd.add + ' ' + format(subscription_name))
        except WebSocketClosedError as ws_error:
            await Log.error(str(ws_error))
            return False

        return True

    async def _on_message_received(self, message):
        #  Log.debug('_on_message_received: message ' + message)
        REDIS_CLIENT.publish(WS_MONITOR_CHANNEL_OUT, message)

    async def _close_connection(self):
        if self._ws_connection:
            Log.debug(_('{} Closing ws connection {}').format(__class__.__name__, self._controller_id))  # noqa
            try:
                self._ws_connection.close()
            except Exception as E:
                await Log.debug(str(E))
