# -*- coding: utf-8 -*-
import asyncio

from asyncpg.exceptions._base import PostgresError

import redis

from tornado.websocket import WebSocketClosedError
from tornado.websocket import websocket_connect

from common.languages import _local_
from common.log.journal import system_logger
from common.models.controller import Controller
from common.settings import WS_MONITOR_CHANNEL_OUT, WS_PING_INTERVAL, WS_PING_TIMEOUT
from common.subscription_sources import CONTROLLER_SUBSCRIPTIONS_LIST, SubscriptionCmd
from common.utils import cancel_async_task
from common.veil.veil_gino import Status
from common.veil.veil_redis import REDIS_CLIENT

# TODO: в событиях журнала задействовать отдельный entity для монитора ресурсов


class ResourcesMonitor:
    """Monitoring of controller events."""

    RECONNECT_TIMEOUT = 15
    CONTROLLER_CHECK_TIMEOUT = 15

    def __init__(self):
        super().__init__()
        self._ws_connection = None
        self._running_flag = True
        self._controller_id = None

        self._controller_online_task = None
        self._resources_monitor_task = None

    # PUBLIC METHODS
    def start(self, controller_id):

        self._controller_id = controller_id
        self._running_flag = True

        native_loop = asyncio.get_event_loop()
        # controller check
        self._controller_online_task = native_loop.create_task(
            self._controller_online_checking()
        )
        # ws data
        self._resources_monitor_task = native_loop.create_task(
            self._processing_ws_messages()
        )

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
        """Смотрим статус контроллера. Если контроллер деактивирован, то проверяем его доступность.

        Если все хорошо, то активируем.
        """
        while self._running_flag:

            await asyncio.sleep(self.CONTROLLER_CHECK_TIMEOUT)

            controller = None
            connection_is_ok = None
            try:
                controller = await Controller.get(self._controller_id)
                # Если контроллер деактивирован (FAILED), то проверяем его доступность.
                # Если статус BAD_AUTH, то ничего не делаем. Эту проблему может решить только юзер
                if controller and controller.status == Status.FAILED:
                    connection_is_ok = await controller.is_ok()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa
                # Если возникло какое-либо исключение, то считаем проверка не пройдена.
                connection_is_ok = False

            # activate
            # Если контроллер есть в бд, если проверка состоялась и если проверка показала,
            # что контроллер доступен, то активируем
            if controller and connection_is_ok:
                await controller.activate()

    async def _processing_ws_messages(self):
        """Listen for data from controller.

        :return:
        """
        while self._running_flag:
            is_connected = await self._connect()
            await system_logger.debug(
                _local_("{} is connected: {}.").format(__class__.__name__, is_connected)
            )  # noqa
            # reconnect if not connected
            if not is_connected:
                await asyncio.sleep(self.RECONNECT_TIMEOUT)
                continue

            # receive messages
            while self._running_flag:
                msg = await self._ws_connection.read_message()
                if msg is None:  # according to doc it means that connection closed
                    await system_logger.warning(
                        "{} Probably connection is closed by server.".format(
                            __class__.__name__
                        )
                    )  # noqa
                    break
                elif "token error" in msg:
                    await system_logger.warning(
                        "{} token error. Closing connection.".format(__class__.__name__)
                    )  # noqa
                    # Если токен эррор, то закрываем соединение и и переходим к попыткам коннекта (начало первого while)
                    await self._close_connection()
                    break
                else:
                    await self._on_message_received(msg)

            await asyncio.sleep(self.RECONNECT_TIMEOUT)

    async def _connect(self):
        try:
            controller = await Controller.get(self._controller_id)
        except PostgresError as ex:
            await system_logger.error(str(ex))
            return False

        # check if controller active
        if not controller or not controller.active:
            return False

        # get token from db
        try:
            token = controller.token.split()[1]
        except IndexError:
            await system_logger.warning("{} Cant get token for controller.").format(
                __class__.__name__
            )
            return False

        # create ws connection
        try:
            connect_url = "ws://{}/ws/?token={}".format(controller.address, token)
            # await system_logger.debug('ws connection url is {}'.format(connect_url))
            self._ws_connection = await websocket_connect(
                url=connect_url,
                ping_interval=WS_PING_INTERVAL,
                ping_timeout=WS_PING_TIMEOUT,
            )
        except Exception as ex:  # noqa
            # Причин для исключения может быть множество включая OS specific
            msg = _local_("Resource monitor can`t connect to controller {}.").format(
                controller.address)
            await system_logger.error(message=msg, description=str(ex))
            return False

        # subscribe to events on controller
        try:
            for subscription_name in CONTROLLER_SUBSCRIPTIONS_LIST:
                await self._ws_connection.write_message(
                    SubscriptionCmd.add + " " + format(subscription_name)
                )
        except WebSocketClosedError:
            return False
        except IOError as ex:
            await self._close_connection()
            await system_logger.error(str(ex))
            return False

        return True

    async def _on_message_received(self, message):
        # await system_logger.debug('_on_message_received: message ' + message)
        try:
            REDIS_CLIENT.publish(WS_MONITOR_CHANNEL_OUT, message)
        except redis.RedisError as ex:
            await system_logger.error(message="Resource monitor ws. Redis error.",
                                      description=str(ex))

    async def _close_connection(self):
        if self._ws_connection:
            await system_logger.debug(
                _local_("Closing ws connection {}.").format(self._controller_id)
            )
            try:
                self._ws_connection.close()
            except Exception as E:
                await system_logger.debug(str(E))
