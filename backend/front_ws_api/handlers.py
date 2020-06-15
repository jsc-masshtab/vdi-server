# -*- coding: utf-8 -*-
from abc import ABC
import asyncio
import time
from typing import Any

import tornado.ioloop
from tornado import httputil
from tornado import websocket
from tornado.web import Application

from front_ws_api.subscription_sources import VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST, SubscriptionCmd

from languages import lang_init
from journal.journal import Log as log

from redis_broker import INTERNAL_EVENTS_CHANNEL, WS_MONITOR_CHANNEL_OUT, REDIS_CLIENT, REDIS_ASYNC_TIMEOUT


_ = lang_init()

# TODO: auth check?


class AbstractSubscriptionObserver(ABC):

    def __init__(self):
        self._subscriptions = []
        self._message_queue = asyncio.Queue(100)  # 100 - max queue size
        self._default_ms_process_timeout = 0.05

    def get_subscriptions(self):
        """
        List of current subscriptions
        :return:
        """
        return self._subscriptions


class VdiFrontWsHandler(websocket.WebSocketHandler, AbstractSubscriptionObserver):  # noqa

    def __init__(self, application: Application, request: httputil.HTTPServerRequest, **kwargs: Any):
        websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
        AbstractSubscriptionObserver.__init__(self)

        self._send_messages_task = None
        # log.debug(_('init VdiFrontWsHandler'))

    def __del__(self):
        log.debug(_('destructor VdiFrontWsHandler'))

    # todo: security problems. implement proper origin checking
    def check_origin(self, origin):
        return True

    async def open(self):
        # log.debug(_('WebSocket opened'))
        loop = asyncio.get_event_loop()
        self._send_messages_task = loop.create_task( self._send_messages_co())

    async def on_message(self, message):
        log.debug(_('Message: {}').format(message))
        response = {'msg_type': 'control', 'error': False}
        # determine if message contains subscription command ('delete /domains/' for example)
        try:
            subscription_cmd, subscription_source = message.split(' ')
            response['msg'] = subscription_cmd
            response['resource'] = subscription_source
        except ValueError as E:
            response['error'] = True
            await self.write_msg(response)
            return
        # check if allowed
        if subscription_source not in VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST:
            await log.error(_('Unknown subscription source'))
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
            log.debug(_('already subscribed'))
            response['error'] = True
        # if 'delete' cmd and not subscribed  then do nothing
        elif subscription_cmd == SubscriptionCmd.delete and subscription_source not in self._subscriptions:
            log.debug(_('not subscribed'))
            response['error'] = True
        # if 'delete' cmd and subscribed then unsubscribe
        elif subscription_cmd == SubscriptionCmd.delete and subscription_source in self._subscriptions:
            self._subscriptions.remove(subscription_source)
            response['error'] = False

        # send response
        await self.write_msg(response)

    def on_close(self):
        log.debug(_('WebSocket closed'))
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
                redis_message = redis_subscriber.get_message()
                # todo: check if message from desired source (self._subscriptions)
                if redis_message:
                    await self.write_msg(redis_message)

                await asyncio.sleep(REDIS_ASYNC_TIMEOUT)

            except Exception as ex:
                await log.error(ex)

    async def write_msg(self, msg):
        try:
            await self.write_message(msg)
        except tornado.websocket.WebSocketClosedError:
            log.debug(_('Write error'))
