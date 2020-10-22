# -*- coding: utf-8 -*-
import asyncio
import json
from typing import Any, Optional, Awaitable

import tornado.ioloop
from tornado import httputil
from tornado import websocket
from tornado.web import Application

from web_app.front_ws_api.subscription_sources import VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST, SubscriptionCmd

from common.languages import lang_init
from common.log.journal import system_logger

from common.veil.veil_redis import INTERNAL_EVENTS_CHANNEL, WS_MONITOR_CHANNEL_OUT, REDIS_CLIENT, a_redis_get_message


_ = lang_init()

# TODO: auth check?


class VdiFrontWsHandler(websocket.WebSocketHandler):  # noqa

    def __init__(self, application: Application, request: httputil.HTTPServerRequest, **kwargs: Any):
        websocket.WebSocketHandler.__init__(self, application, request, **kwargs)

        # subscription sources
        self._subscriptions = []

        self._send_messages_task = None
        # await system_logger.debug(_('init VdiFrontWsHandler'))

    # todo: security problems. implement proper origin checking
    def check_origin(self, origin):
        return True

    async def open(self):
        await system_logger.debug(_('WebSocket opened.'))
        loop = asyncio.get_event_loop()
        self._send_messages_task = loop.create_task(self._send_messages_co())

    async def on_message(self, message):
        await system_logger.debug(_('Message: {}.').format(message))
        response = {'msg_type': 'control', 'error': False}
        # determine if message contains subscription command ('delete /domains/' for example)
        try:
            subscription_cmd, subscription_source = message.split(' ')
            response['msg'] = subscription_cmd
            response['resource'] = subscription_source
        except ValueError:
            response['error'] = True
            await self.write_msg(response)
            return
        # check if allowed
        if subscription_source not in VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST:
            msg = _('WS listener error.')
            description = _('Unknown subscription source.')
            await system_logger.error(message=msg, description=description)
            response['error'] = True
            await self.write_msg(response)
            return
        # print('Test Length', len(self._subscriptions))
        # if 'add' cmd and not subscribed  then subscribe
        if subscription_cmd == SubscriptionCmd.add and subscription_source not in self._subscriptions:
            self._subscriptions.append(subscription_source)
            response['error'] = False
        # if 'add' cmd and subscribed then do nothing
        elif subscription_cmd == SubscriptionCmd.add and subscription_source in self._subscriptions:
            await system_logger.debug(_('Already subscribed.'))
            response['error'] = True
        # if 'delete' cmd and not subscribed  then do nothing
        elif subscription_cmd == SubscriptionCmd.delete and subscription_source not in self._subscriptions:
            await system_logger.debug(_('Not subscribed.'))
            response['error'] = True
        # if 'delete' cmd and subscribed then unsubscribe
        elif subscription_cmd == SubscriptionCmd.delete and subscription_source in self._subscriptions:
            self._subscriptions.remove(subscription_source)
            response['error'] = False

        # send response
        await self.write_msg(response)

    def on_close(self):
        try:
            self._send_messages_task.cancel()
        except asyncio.CancelledError:
            pass

    async def _send_messages_co(self):
        """wait for message and send it to front client"""

        # subscribe to channels  INTERNAL_EVENTS_CHANNEL and WS_MONITOR_CHANNEL_OUT
        redis_subscriber = REDIS_CLIENT.pubsub()
        redis_subscriber.subscribe(INTERNAL_EVENTS_CHANNEL, WS_MONITOR_CHANNEL_OUT)

        while True:
            try:
                redis_message = await a_redis_get_message(redis_subscriber)

                if redis_message['type'] == 'message':
                    redis_message_data = redis_message['data'].decode()
                    redis_message_data_dict = json.loads(redis_message_data)

                    # Шлем только те сообщения, которые хочет фронт
                    if redis_message_data_dict['resource'] in self._subscriptions:
                        # print("_send_messages_co: redis_message_data ", redis_message_data)
                        await self.write_msg(redis_message_data)

            except asyncio.CancelledError:
                break
            except Exception as ex:
                await system_logger.debug(str(ex))

    async def write_msg(self, msg):
        try:
            await self.write_message(msg)
        except tornado.websocket.WebSocketError:
            await system_logger.debug(_('Write error.'))

    # unused abstract method implementation
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass
