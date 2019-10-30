# -*- coding: utf-8 -*-
import tornado.ioloop

from tornado import websocket
from tornado import gen
from  tornado.web import Application
from tornado import gen, httpclient, httputil
import tornado.ioloop

from typing import Any

import asyncio
from abc import ABC

from .resources_monitoring_data import VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST, SubscriptionCmd

from resources_monitoring.resources_monitor_manager import resources_monitor_manager


class AbstractSubscriptionObserver(ABC):

    def __init__(self):
        self._subscriptions = []
        self._message_queue = asyncio.Queue(100)  # 100 - max queue size
        self._default_ms_process_timeout = 0.1

    # PUBLIC METHODS
    def on_notified(self, json_message):
        """
        invoked by monitor when message received
        :param json_message:
        :return:
        """
        # print(__class__.__name__, json_message)
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


class VdiFrontWsHandler(websocket.WebSocketHandler, AbstractSubscriptionObserver):

    def __init__(self, application: Application, request: httputil.HTTPServerRequest, **kwargs: Any):
        websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
        AbstractSubscriptionObserver.__init__(self)
        print('init VdiFrontWsHandler')

    def __del__(self):
        print('destructor VdiFrontWsHandler')

    # todo: security problems. implement proper origin checking
    def check_origin(self, origin):
        return True

    async def open(self):
        print("WebSocket opened")
        self._start_message_sending()
        resources_monitor_manager.subscribe(self)

    async def on_message(self, message):
        print('message', message)

        response_dict = {'msg_type': 'control', 'error': False}
        # determine if message contains subscription command ('delete /domains/' for example)
        try:
            subscription_cmd, subscription_source = message.split(' ')
            response_dict['msg'] = subscription_cmd
            response_dict['resource'] = subscription_source
        except ValueError:
            response_dict['error'] = True
            await self._write_msg(response_dict)
            return
        # check if allowed
        if subscription_source not in VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST:
            print(__class__.__name__, ' Unknown subscription source')
            response_dict['error'] = True
            await self._write_msg(response_dict)
            return
        # print('Test Length', len(self._subscriptions))
        # if 'add' cmd and not subscribed  then subscribe
        if subscription_cmd == SubscriptionCmd.add and subscription_source not in self._subscriptions:
            self._subscriptions.append(subscription_source)
            response_dict['error'] = False
        # if 'add' cmd and subscribed then do nothing
        elif subscription_cmd == SubscriptionCmd.add and subscription_source in self._subscriptions:
            print(__class__.__name__, 'already subscribed')
            response_dict['error'] = True
        # if 'delete' cmd and not subscribed  then do nothing
        elif subscription_cmd == SubscriptionCmd.delete and subscription_source not in self._subscriptions:
            print(__class__.__name__, 'not subscribed')
            response_dict['error'] = True
        # if 'delete' cmd and subscribed then unsubscribe
        elif subscription_cmd == SubscriptionCmd.delete and subscription_source in self._subscriptions:
            self._subscriptions.remove(subscription_source)
            response_dict['error'] = False

        # send response
        await self._write_msg(response_dict)

    def on_close(self):
        print("WebSocket closed")
        resources_monitor_manager.unsubscribe(self)
        #await self._stop_message_sending()

    def _start_message_sending(self):
        """start message sending task"""
        self._send_messages_task = tornado.ioloop.IOLoop.current().add_callback(self._send_messages_co)

    async def _stop_message_sending(self):
        """stop message sending corutine"""
        self._send_messages_flag = False
        if self._send_messages_task:
            await self._send_messages_task

    async def _send_messages_co(self):
        """wait for message and send it to front client"""
        self._send_messages_flag = True
        while self._send_messages_flag:
            await asyncio.sleep(self._default_ms_process_timeout)
            try:
                json_message = self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                continue
            await self._write_msg(json_message)

    async def _write_msg(self, msg):
        try:
            await self.write_message(msg)
        except tornado.websocket.WebSocketClosedError:
            print(__class__.__name__, 'write error')


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
            print(__class__.__name__, 'json_message', json_message)
            if predicate(json_message):
                return True

        return False