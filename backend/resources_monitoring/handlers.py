# -*- coding: utf-8 -*-
from abc import ABC
import logging
import asyncio
import time
from typing import Any

import tornado.ioloop
from tornado import httputil
from tornado import websocket
from tornado.web import Application

from resources_monitoring.resources_monitoring_data import VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST, SubscriptionCmd
from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from resources_monitoring.internal_event_monitor import internal_event_monitor

from languages import lang_init


_ = lang_init()

application_log = logging.getLogger('tornado.application')
# TODO: auth check?

# class ClientManager:
#     clients = []
#
#     def __init__(self):
#         pass
#
#     async def send_message(self, msg):
#         for client in self.clients:
#             await client.write_msg(msg)
#
#     def add_client(self, client):
#         self.clients.append(client)
#
#     def remove_client(self, client):
#         self.clients.remove(client)


class AbstractSubscriptionObserver(ABC):

    def __init__(self):
        self._subscriptions = []
        self._message_queue = asyncio.Queue(100)  # 100 - max queue size
        self._default_ms_process_timeout = 0.05

    # PUBLIC METHODS
    def on_notified(self, json_message):
        """
        invoked by monitor when message received
        :param json_message:
        :return:
        """
        try:
            self._message_queue.put_nowait(json_message)
        except asyncio.QueueFull:
            pass

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

        self._send_messages_flag = False
        # application_log.debug(_('init VdiFrontWsHandler'))

    def __del__(self):
        application_log.debug(_('destructor VdiFrontWsHandler'))

    # todo: security problems. implement proper origin checking
    def check_origin(self, origin):
        return True

    async def open(self):
        # application_log.debug(_('WebSocket opened'))
        self._start_message_sending()
        resources_monitor_manager.subscribe(self)
        internal_event_monitor.subscribe(self)

    async def on_message(self, message):
        application_log.debug(_('Message: ').format(message))
        response_dict = {'msg_type': 'control', 'error': False}
        # determine if message contains subscription command ('delete /domains/' for example)
        try:
            subscription_cmd, subscription_source = message.split(' ')
            response_dict['msg'] = subscription_cmd
            response_dict['resource'] = subscription_source
        except ValueError:
            response_dict['error'] = True
            await self.write_msg(response_dict)
            return
        # check if allowed
        if subscription_source not in VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST:
            application_log.error(_('Unknown subscription source'))
            response_dict['error'] = True
            await self.write_msg(response_dict)
            return
        # print('Test Length', len(self._subscriptions))
        # if 'add' cmd and not subscribed  then subscribe
        if subscription_cmd == SubscriptionCmd.add and subscription_source not in self._subscriptions:
            self._subscriptions.append(subscription_source)
            response_dict['error'] = False
        # if 'add' cmd and subscribed then do nothing
        elif subscription_cmd == SubscriptionCmd.add and subscription_source in self._subscriptions:
            application_log.debug(_('already subscribed'))
            response_dict['error'] = True
        # if 'delete' cmd and not subscribed  then do nothing
        elif subscription_cmd == SubscriptionCmd.delete and subscription_source not in self._subscriptions:
            application_log.debug(_('not subscribed'))
            response_dict['error'] = True
        # if 'delete' cmd and subscribed then unsubscribe
        elif subscription_cmd == SubscriptionCmd.delete and subscription_source in self._subscriptions:
            self._subscriptions.remove(subscription_source)
            response_dict['error'] = False

        # send response
        await self.write_msg(response_dict)

    def on_close(self):
        application_log.debug(_('WebSocket closed'))
        resources_monitor_manager.unsubscribe(self)
        internal_event_monitor.unsubscribe(self)

        self._send_messages_flag = False
        tornado.ioloop.IOLoop.instance().remove_timeout(self._send_messages_task)

    def _start_message_sending(self):
        """start message sending task"""
        self._send_messages_task = tornado.ioloop.IOLoop.instance().add_timeout(time.time(), self._send_messages_co)

    # async def _stop_message_sending(self):
    #     """stop message sending corutine"""
    #     self._send_messages_flag = False
    #     if self._send_messages_task:
    #         await self._send_messages_task

    async def _send_messages_co(self):
        """wait for message and send it to front client"""
        self._send_messages_flag = True
        while self._send_messages_flag:
            await asyncio.sleep(self._default_ms_process_timeout)
            try:
                json_message = self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                continue
            await self.write_msg(json_message)

    async def write_msg(self, msg):
        try:
            await self.write_message(msg)
        except tornado.websocket.WebSocketClosedError:
            application_log.debug(_('Write error'))


class WaiterSubscriptionObserver(AbstractSubscriptionObserver):

    def __init__(self):
        super().__init__()

    def add_subscription_source(self, subscription_source):
        if subscription_source not in self._subscriptions:
            self._subscriptions.append(subscription_source)

    # PUBLIC METHODS
    async def wait_for_message(self, predicate, timeout):
        """
        Wait for message until timeout reached.

        :param predicate:  condition to find required message. Signature: def fun(json_message) -> bool
        :param timeout: time to wait. seconds
        :return bool: return true if awaited message received. Return false if timeuot expired and
         awaited message is not received
        """
        await_time = 0
        while True:
            # stop if time expired
            if await_time >= timeout:
                return False
            # count time
            await_time += self._default_ms_process_timeout

            await asyncio.sleep(self._default_ms_process_timeout)
            # try to receive message
            try:
                json_message = self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                continue
            # application_log.debug('WS message: {}'.format(json_message))
            if predicate(json_message):
                return True

        return False
