# -*- coding: utf-8 -*-
import asyncio
import json
from json.decoder import JSONDecodeError
from typing import Any

from tornado import httputil
from tornado.web import Application

from common.languages import _local_
from common.log.journal import system_logger
from common.settings import (
    INTERNAL_EVENTS_CHANNEL,
    REDIS_TEXT_MSG_CHANNEL,
    WS_MONITOR_CHANNEL_OUT,
)
from common.subscription_sources import (
    SubscriptionCmd,
    USERS_SUBSCRIPTION,
    VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST,
    WsMessageDirection,
    WsMessageType
)
from common.veil.auth.veil_jwt import jwtauth_ws
from common.veil.veil_handlers import BaseWsHandler
from common.veil.veil_redis import REDIS_CLIENT, a_redis_get_message


@jwtauth_ws
class VdiFrontWsHandler(BaseWsHandler):  # noqa
    def __init__(
        self,
        application: Application,
        request: httputil.HTTPServerRequest,
        **kwargs: Any
    ):
        super().__init__(application, request, **kwargs)

        # subscription sources
        self._subscriptions = []
        self._send_messages_task = None

    async def open(self):

        # on success
        await system_logger.debug(_local_("WebSocket opened."))
        loop = asyncio.get_event_loop()
        self._send_messages_task = loop.create_task(self._send_messages_co())

    async def on_message(self, message):
        await system_logger.debug(_local_("Message: {}.").format(message))
        await self._check_for_subscription_cmd(message)

    def on_close(self):
        try:
            if self._send_messages_task:
                self._send_messages_task.cancel()
        except asyncio.CancelledError:
            pass

    async def _check_for_subscription_cmd(self, command):
        """Проверить есть ли команда для подписки и подписаться."""
        response = {"msg_type": WsMessageType.CONTROL.value, "error": False}
        # determine if message contains subscription command ('delete /domains/' for example)
        try:
            subscription_cmd, subscription_source = command.split(" ")
            response["msg"] = subscription_cmd
            response["resource"] = subscription_source
        except ValueError:
            response["error"] = True
            await self.write_msg(response)
            return
        # check if allowed
        if subscription_source not in VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST:
            msg = _local_("WS listener error.")
            description = _local_("Unknown subscription source.")
            await system_logger.error(message=msg, description=description)
            response["error"] = True
            await self.write_msg(response)
            return
        # if 'add' cmd and not subscribed  then subscribe
        if (
            subscription_cmd == SubscriptionCmd.add
            and subscription_source not in self._subscriptions  # noqa: W503
        ):
            self._subscriptions.append(subscription_source)
            response["error"] = False
        # if 'add' cmd and subscribed then do nothing
        elif (
            subscription_cmd == SubscriptionCmd.add
            and subscription_source in self._subscriptions  # noqa: W503
        ):
            await system_logger.debug(_local_("Already subscribed."))
            response["error"] = True
        # if 'delete' cmd and not subscribed  then do nothing
        elif (
            subscription_cmd == SubscriptionCmd.delete
            and subscription_source not in self._subscriptions  # noqa: W503
        ):
            await system_logger.debug(_local_("Not subscribed."))
            response["error"] = True
        # if 'delete' cmd and subscribed then unsubscribe
        elif (
            subscription_cmd == SubscriptionCmd.delete
            and subscription_source in self._subscriptions  # noqa: W503
        ):
            self._subscriptions.remove(subscription_source)
            response["error"] = False

        # send response
        await self.write_msg(response)

    async def _send_messages_co(self):
        """Wait for message and send it to front client."""
        # subscribe to channels  INTERNAL_EVENTS_CHANNEL and WS_MONITOR_CHANNEL_OUT
        redis_subscriber = REDIS_CLIENT.pubsub()
        redis_subscriber.subscribe(
            INTERNAL_EVENTS_CHANNEL, WS_MONITOR_CHANNEL_OUT, REDIS_TEXT_MSG_CHANNEL
        )

        while True:
            try:
                redis_message = await a_redis_get_message(redis_subscriber)

                if redis_message["type"] == "message":
                    redis_message_data = redis_message["data"].decode()
                    redis_message_data_dict = json.loads(redis_message_data)

                    resource = redis_message_data_dict.get("resource")
                    if not resource:
                        continue

                    elif resource in self._subscriptions:
                        # USERS_SUBSCRIPTION resource
                        if resource == USERS_SUBSCRIPTION:
                            if (
                                redis_message_data_dict["msg_type"]
                                == WsMessageType.TEXT_MSG.value  # noqa: W503
                                and redis_message_data_dict["direction"]  # noqa: W503
                                == WsMessageDirection.USER_TO_ADMIN.value  # noqa: W503
                            ):
                                # Текстовые сообщения (от пользователей ТК) администратору
                                await self.write_msg(redis_message_data)
                        # other resources
                        else:
                            # print("_send_messages_co: redis_message_data ", redis_message_data)
                            await self.write_msg(redis_message_data)

            except asyncio.CancelledError:
                break
            except (KeyError, ValueError, TypeError, JSONDecodeError) as ex:
                await system_logger.debug(
                    message="Sending msg error in frontend ws handler.",
                    description=str(ex),
                )
