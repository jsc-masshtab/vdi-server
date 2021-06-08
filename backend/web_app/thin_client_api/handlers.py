# -*- coding: utf-8 -*-
import asyncio
import json
import textwrap
from abc import ABC
from json.decoder import JSONDecodeError
from typing import Any

from aiohttp import client_exceptions

from sqlalchemy.sql import func

from tornado import httputil
from tornado.web import Application

from veil_api_client import DomainTcpUsb, VeilRetryConfiguration

from common.languages import lang_init
from common.log.journal import system_logger
from common.models.active_tk_connection import ActiveTkConnection
from common.models.pool import AutomatedPool, Pool as PoolM, RdsPool
from common.models.task import PoolTaskType, Task, TaskStatus
from common.settings import (
    REDIS_DB, REDIS_PASSWORD, REDIS_PORT, REDIS_TEXT_MSG_CHANNEL,
    REDIS_THIN_CLIENT_CHANNEL, REDIS_THIN_CLIENT_CMD_CHANNEL,
    WS_MONITOR_CHANNEL_OUT
)
from common.subscription_sources import (
    USERS_SUBSCRIPTION, WsMessageDirection, WsMessageType
)
from common.veil.auth.veil_jwt import jwtauth
from common.veil.veil_handlers import BaseHandler, BaseWsHandler
from common.veil.veil_redis import (
    REDIS_CLIENT,
    ThinClientCmd,
    a_redis_get_message,
    request_to_execute_pool_task,
)

_ = lang_init()


@jwtauth
class RedisInfoHandler(BaseHandler, ABC):
    """Данные для подключения тонких клиентов к Redis."""

    async def get(self):
        """  # noqa
        {
            "data": {
                "port": 6379,
                "password": "veil",
                "channel": "TC_CHANNEL"
                "db": 0:
            }
        }
        """
        redis_info = dict(
            port=REDIS_PORT,
            channel=REDIS_THIN_CLIENT_CHANNEL,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
        )
        response = dict(data=redis_info)
        return self.finish(response)


@jwtauth
class PoolHandler(BaseHandler, ABC):
    """Возвращает все пулы пользователя."""

    async def get(self):
        user = await self.get_user_model_instance()
        pools = await user.pools
        response = {"data": pools}

        await system_logger.info(
            _("User {} requested pools data.").format(user.username),
            entity=user.entity,
            user=user.username,
        )
        return await self.log_finish(response)


@jwtauth
class PoolGetVm(BaseHandler, ABC):
    """Получает конкретную ВМ пользователя."""

    async def post(self, pool_id):
        remote_protocol = self.args.get(
            "remote_protocol", PoolM.PoolConnectionTypes.SPICE.name
        )
        # Проверяем лимит клиентов
        if PoolM.thin_client_limit_exceeded():
            response = {
                "errors": [{"message": _("Thin client limit exceeded."),
                            "code": "001"}]
            }
            return await self.log_finish(response)
        user = await self.get_user_model_instance()
        pool = await PoolM.get(pool_id)
        if not pool:
            response = {
                "errors": [{"message": _("Pool not found."), "code": "404"}]}
            return await self.log_finish(response)
        # Проверяем разрешен ли присланный remote_protocol для данного пула
        con_t = pool.connection_types
        bad_connection_type = remote_protocol not in PoolM.PoolConnectionTypes.values() or \
                              PoolM.PoolConnectionTypes[remote_protocol] not in con_t  # noqa: E127
        if bad_connection_type:
            response = {
                "errors": [
                    {
                        "message": _(
                            "The pool doesnt support connection type {}."
                        ).format(remote_protocol),
                        "code": "404",
                    }
                ]
            }
            return await self.log_finish(response)
        pool_type = await pool.pool_type
        expandable_pool = False  # В данный момент расширится может автоматический (гостевой пул)
        if pool_type == PoolM.PoolTypes.AUTOMATED or pool_type == PoolM.PoolTypes.GUEST:
            # Запрос на расширение пула
            auto_pool = await AutomatedPool.get(pool.id)
            expandable_pool = True
        vm = await pool.get_vm(user_id=user.id)
        if not vm:  # ВМ для пользователя не присутствует
            # В случае RDS пула выдаем общий для всех RDS Сервер
            if pool_type == PoolM.PoolTypes.RDS:
                vms = await pool.vms
                vm = vms[0]
            else:
                # Если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
                vm = await pool.get_free_vm_v2()

            # Если свободная VM найдена, нужно закрепить ее за пользователем.
            if vm:
                await vm.add_user(user.id, creator="system")
                if expandable_pool:
                    await self._expand_pool_if_required(pool)
            elif expandable_pool and not await auto_pool.check_if_total_size_reached():
                response = {
                    "errors": [
                        {
                            "message": _(
                                "The pool doesn`t have free machines. Try again after 5 minutes."
                            ),
                            "code": "002",
                        }
                    ]
                }
                await self._expand_pool_if_required(pool)
                return await self.log_finish(response)
            else:
                response = {
                    "errors": [
                        {
                            "message": _("The pool doesn`t have free machines."),
                            "code": "003",
                        }
                    ]
                }
                return await self.log_finish(response)

        elif expandable_pool:  # Даже если у пользователя есть ВМ, то попробовать расшириться все равно нужно
            await self._expand_pool_if_required(pool)
        # TODO: обработка новых исключений
        # Только включение ВМ.
        try:
            # Дальше запросы начинают уходить на veil
            veil_domain = await vm.vm_client
            if not veil_domain:
                raise client_exceptions.ServerDisconnectedError()
            await veil_domain.info()
            if not veil_domain.powered:
                await vm.start()

        except client_exceptions.ServerDisconnectedError:
            response = {
                "errors": [
                    {"message": _("VM is unreachable on ECP VeiL."), "code": "004"}
                ]
            }
            return await self.log_finish(response)
        # Актуализируем данные для подключения
        info = await veil_domain.info()

        await system_logger.info(
            _("User {} connected to pool {}.").format(user.username, pool.verbose_name),
            entity=pool.entity,
            user=user.username,
        )
        await system_logger.info(
            _("User {} connected to VM {}.").format(user.username, vm.verbose_name),
            entity=vm.entity,
            user=user.username,
        )
        # TODO: использовать veil_domain.hostname вместо IP

        # Определяем адрес и порт в зависимости от протокола
        vm_controller = await vm.controller
        # Проверяем наличие клиента у контроллера
        veil_client = vm_controller.veil_client
        if not veil_client:
            response = {
                "errors": [{"message": _("The remote controller is unavailable.")}]
            }
            return await self.log_finish(response)
        if (
            remote_protocol == PoolM.PoolConnectionTypes.RDP.name
            or remote_protocol  # noqa: W503
            == PoolM.PoolConnectionTypes.NATIVE_RDP.name  # noqa: W503
        ):
            try:
                vm_address = veil_domain.first_ipv4
                if vm_address is None:
                    raise RuntimeError
                vm_port = 3389  # default rdp port

            except (RuntimeError, IndexError, KeyError):
                response = {
                    "errors": [
                        {
                            "message": _(
                                "VM does not support RDP. The controller didn`t provide a VM address."
                            ),
                            "code": "005"
                        }
                    ]
                }
                return await self.log_finish(response)

        elif remote_protocol == PoolM.PoolConnectionTypes.SPICE_DIRECT.name:
            # Нужен адрес сервера поэтому делаем запрос
            node_id = str(veil_domain.node["id"])
            node_info = await vm_controller.veil_client.node(node_id=node_id).info()
            vm_address = node_info.response[0].management_ip
            vm_port = info.data["real_remote_access_port"]

        else:  # PoolM.PoolConnectionTypes.SPICE.name by default
            vm_address = vm_controller.address
            vm_port = veil_domain.remote_access_port

        permissions = await user.get_permissions()
        try:
            farm_list = await RdsPool.get_farm_list(pool.id, user.username) \
                if pool_type == PoolM.PoolTypes.RDS else []
        except (KeyError, JSONDecodeError, RuntimeError) as ex:
            response = {"errors": [{"message": _("Unable to get list of published applications. {}.").format(str(ex))}]}
            return await self.log_finish(response)
        response = {
            "data": dict(
                host=vm_address,
                port=vm_port,
                password=veil_domain.graphics_password,
                vm_verbose_name=veil_domain.verbose_name,
                vm_controller_address=vm_controller.address,
                vm_id=str(vm.id),
                permissions=[permission.value for permission in permissions],
                farm_list=farm_list,
                pool_type=pool_type
            )
        }
        return await self.log_finish(response)

    @staticmethod
    async def _expand_pool_if_required(pool_model):
        """Только если расширение возможно и над пулом не выполняются другие задачи расширения."""  # noqa: E501
        if not pool_model:
            return
        # 1) is max reached
        auto_pool = await AutomatedPool.get(pool_model.id)
        total_size_reached = await auto_pool.check_if_total_size_reached()
        # 2) is not enough free vms
        is_not_enough_free_vms = await auto_pool.check_if_not_enough_free_vms()
        # 3) other tasks
        tasks = await Task.get_tasks_associated_with_entity(
            pool_model.id, TaskStatus.IN_PROGRESS, PoolTaskType.POOL_EXPAND
        )

        if not total_size_reached and not tasks and is_not_enough_free_vms:
            await request_to_execute_pool_task(pool_model.id, PoolTaskType.POOL_EXPAND)


@jwtauth
class VmAction(BaseHandler, ABC):
    """Пересылка действия над ВМ на ECP VeiL."""

    async def post(self, pool_id, action):

        user = await self.get_user_model_instance()
        vm = await BaseHandler.validate_and_get_vm(user, pool_id)

        try:
            force = self.args.get("force", False)
            # Все возможные проверки закончились - приступаем.
            is_action_successful = await vm.action(action_name=action, force=force)
            response = {"data": "success"}
        except AssertionError as vm_action_error:
            response = {"errors": [{"message": str(vm_action_error)}]}
            is_action_successful = False

        # log action
        if is_action_successful:
            msg = _("User {} executed action {} on VM {}.")
        else:
            msg = _("User {} failed to execute action {} on VM {}.")
        await system_logger.info(
            msg.format(user.username, action, vm.verbose_name),
            entity=vm.entity,
            user=user.username,
        )

        return await self.log_finish(response)


@jwtauth
class AttachUsb(BaseHandler, ABC):
    """Добавить usb tcp редирект девайс."""

    async def post(self, pool_id):

        host_address = self.validate_and_get_parameter("host_address")
        host_port = self.validate_and_get_parameter("host_port")

        user = await self.get_user_model_instance()
        vm = await BaseHandler.validate_and_get_vm(user, pool_id)

        # attach request
        try:
            vm_controller = await vm.controller
            veil_client = vm_controller.veil_client.domain(
                domain_id=vm.id_str,
                retry_opts=VeilRetryConfiguration(num_of_attempts=0),
            )

            if not veil_client:
                raise AssertionError(_("VM has no api client."))
            domain_tcp_usb_params = DomainTcpUsb(host=host_address, service=host_port)
            controller_response = await veil_client.attach_usb(
                action_type="tcp_usb_device",
                tcp_usb=domain_tcp_usb_params,
                no_task=True,
            )
            return await self.log_finish(controller_response.data)

        except AssertionError as error:
            response = {"errors": [{"message": str(error)}]}
        return await self.log_finish(response)


@jwtauth
class DetachUsb(BaseHandler, ABC):
    """Убрать usb tcp редирект девайс."""

    async def post(self, pool_id):

        usb_uuid = self.args.get("usb_uuid")
        remove_all = self.args.get("remove_all", False)

        user = await self.get_user_model_instance()
        vm = await BaseHandler.validate_and_get_vm(user, pool_id)

        # detach request
        try:
            veil_client = await vm.vm_client
            if not veil_client:
                raise AssertionError(_("VM has no api client."))
            controller_response = await veil_client.detach_usb(
                action_type="tcp_usb_device", usb=usb_uuid, remove_all=remove_all
            )
            return await self.log_finish(controller_response.data)

        except AssertionError as error:
            response = {"errors": [{"message": str(error)}]}
        return await self.log_finish(response)


@jwtauth
class SendTextMsgHandler(BaseHandler, ABC):
    """Текстовое сообщение от пользователя ТК.

    Пользователь ТК ничего не знает об админах, поэтому шлет сообщение всем текущим активным администраторам
    в канал REDIS_TEXT_MSG_CHANNEL
    """

    async def post(self):
        user = await self.get_user_model_instance()

        text_message = self.args.get("message")
        if not text_message:
            response = {"errors": [{"message": _("Message can not be empty.")}]}
            return await self.log_finish(response)

        try:
            shorten_msg = textwrap.shorten(text_message, width=2048)

            msg_data_dict = dict(
                message=shorten_msg,
                msg_type=WsMessageType.TEXT_MSG.value,
                direction=WsMessageDirection.USER_TO_ADMIN.value,
                sender_id=str(user.id),
                sender_name=user.username,
                resource=USERS_SUBSCRIPTION,
            )

            REDIS_CLIENT.publish(REDIS_TEXT_MSG_CHANNEL, json.dumps(msg_data_dict))

            response = {"data": "success"}
            return await self.log_finish(response)

        except (KeyError, JSONDecodeError, TypeError) as ex:
            message = _("Wrong message format.") + str(ex)
            response = {"errors": [{"message": message}]}
            return await self.log_finish(response)


class ThinClientWsHandler(BaseWsHandler):
    def __init__(
        self,
        application: Application,
        request: httputil.HTTPServerRequest,
        **kwargs: Any
    ):
        super().__init__(application, request, **kwargs)

        self.conn_id = None
        self._send_messages_task = None
        self._listen_for_cmd_task = None

    async def open(self):
        is_validated = await self._validate_token()
        if not is_validated:
            return

        try:
            # Сохраняем юзера с инфой
            tk_conn = await ActiveTkConnection.soft_create(
                conn_id=self.conn_id,
                is_conn_init_by_user=int(
                    self.get_query_argument(name="is_conn_init_by_user")
                ),
                user_id=self.user_id,
                veil_connect_version=self.get_query_argument("veil_connect_version"),
                vm_id=self.get_query_argument(name="vm_id", default=None),
                tk_ip=self.remote_ip,
                tk_os=self.get_query_argument("tk_os"),
            )
            self.conn_id = tk_conn.id

            response = {
                "msg_type": WsMessageType.CONTROL.value,
                "error": False,
                "msg": "Auth success",
            }
            await self._write_msg(json.dumps(response))

        except Exception as ex:  # noqa
            response = {
                "msg_type": WsMessageType.CONTROL.value,
                "error": True,
                "msg": str(ex),
            }
            await self._write_msg(json.dumps(response))
            self.close(code=4000)

        # start tasks
        loop = asyncio.get_event_loop()
        self._send_messages_task = loop.create_task(self._send_messages_co())
        self._listen_for_cmd_task = loop.create_task(self._listen_for_cmd())

    async def on_message(self, message):
        try:
            recv_data_dict = json.loads(message)
            msg_type = recv_data_dict["msg_type"]

            if msg_type == WsMessageType.UPDATED.value:
                # Сообщение об апдэйте (вм, afk)
                event_type = recv_data_dict["event"]
                tk_conn = await ActiveTkConnection.get(self.conn_id)
                if tk_conn:
                    if event_type == "vm_changed":  # юзер подключился/отключился от машины
                        conn_type = recv_data_dict.get("connection_type")
                        is_conn_secure = recv_data_dict.get("is_connection_secure")
                        await tk_conn.update_vm_data(recv_data_dict["vm_id"], conn_type, is_conn_secure)

                    elif event_type == "user_gui":  # юзер нажал кнопку/кликнул
                        await tk_conn.update_last_interaction()

                    elif event_type == "network_stats":
                        await tk_conn.update_network_stats(**recv_data_dict)

        except (KeyError, ValueError, TypeError, JSONDecodeError) as ex:
            response = {
                "msg_type": WsMessageType.CONTROL.value,
                "error": True,
                "msg": "Wrong msg format " + str(ex),
            }
            await self._write_msg(json.dumps(response))

    def on_close(self):
        # print("!!!WebSocket closed", flush=True)
        loop = asyncio.get_event_loop()
        loop.create_task(self.on_async_close())

        # stop tasks
        if self._send_messages_task:
            self._send_messages_task.cancel()
        if self._listen_for_cmd_task:
            self._listen_for_cmd_task.cancel()

    async def on_async_close(self):
        tk_conn = await ActiveTkConnection.get(self.conn_id)
        if tk_conn:
            await tk_conn.deactivate()

    async def on_pong(self, data: bytes) -> None:
        # print("WebSocket on_pong", flush=True)

        # Обновляем дату последнего сообщения от ТК
        await ActiveTkConnection.update.values(data_received=func.now()).where(
            ActiveTkConnection.id == self.conn_id
        ).gino.status()

    async def _send_messages_co(self):
        """Отсылка сообщений на ТК. Сообщения достаются из редис каналов."""
        redis_subscriber = REDIS_CLIENT.pubsub()
        redis_subscriber.subscribe(WS_MONITOR_CHANNEL_OUT, REDIS_TEXT_MSG_CHANNEL)

        while True:
            try:
                redis_message = await a_redis_get_message(redis_subscriber)

                if redis_message["type"] == "message":
                    redis_message_data = redis_message["data"].decode()
                    redis_message_data_dict = json.loads(redis_message_data)

                    msg_type = redis_message_data_dict.get("msg_type")
                    if not msg_type:
                        continue

                    if msg_type == WsMessageType.DATA.value:
                        # Пересылаем сообщения об апдейте ВМ.
                        if redis_message_data_dict["resource"] == "/domains/":
                            vm_id = await ActiveTkConnection.get_vm_id(self.conn_id)
                            if vm_id and redis_message_data_dict["id"] == str(vm_id):
                                await self._write_msg(redis_message_data)

                    elif (
                        msg_type == WsMessageType.TEXT_MSG.value
                        and redis_message_data_dict["direction"]  # noqa: W503
                        == WsMessageDirection.ADMIN_TO_USER.value  # noqa: W503
                    ):
                        # Посылка текстовых сообщений (от админа) на ТК
                        recipient_id = redis_message_data_dict.get("recipient_id")

                        # Если recipient is None то считаем что  сообщение предназначено для всех текущих
                        # пользователей ТК, если не None, то шлем только указанному
                        if (recipient_id is None) or (
                            recipient_id == str(self.user_id)
                        ):
                            await self._write_msg(redis_message_data)

            except asyncio.CancelledError:
                break
            except (KeyError, ValueError, TypeError, JSONDecodeError) as ex:
                await system_logger.debug(
                    message="Sending msg error in thin client ws handler.",
                    description=str(ex),
                )

    async def _listen_for_cmd(self):
        """Команды от админа."""
        redis_subscriber = REDIS_CLIENT.pubsub()
        redis_subscriber.subscribe(REDIS_THIN_CLIENT_CMD_CHANNEL)

        while True:
            try:
                redis_message = await a_redis_get_message(redis_subscriber)

                if redis_message["type"] == "message":
                    redis_message_data = redis_message["data"].decode()
                    redis_message_data_dict = json.loads(redis_message_data)

                    if (
                        redis_message_data_dict["command"]
                        == ThinClientCmd.DISCONNECT.name  # noqa: W503
                    ):
                        # Завершаем соедниение в зависимости от полученных параметров
                        disconnect_current_tk = False
                        conn_id = redis_message_data_dict.get("conn_id")
                        user_id = redis_message_data_dict.get("user_id")

                        # Команда на закрытие всех соединений
                        if conn_id is None and user_id is None:
                            disconnect_current_tk = True
                        # Команда закрыть конкретное соединение
                        elif conn_id and self.conn_id and conn_id == str(self.conn_id):
                            disconnect_current_tk = True
                        # Команда закрыть соеднинения пользователя
                        elif user_id and self.conn_id:
                            tk_conn = await ActiveTkConnection.get(self.conn_id)
                            current_user_id = tk_conn.user_id
                            if user_id == str(current_user_id):
                                disconnect_current_tk = True

                        if disconnect_current_tk:
                            # Отсылаем клиенту команду. По ней он отключится от машины
                            response = {
                                "msg_type": WsMessageType.CONTROL.value,
                                "cmd": ThinClientCmd.DISCONNECT.name,
                                "error": False,
                                "msg": "Disconnect requested",
                            }
                            await self._write_msg(json.dumps(response))
                            self.close()

            except asyncio.CancelledError:
                break
            except (KeyError, ValueError, TypeError, JSONDecodeError) as ex:
                await system_logger.debug(
                    message="Thin client ws listening commands error.",
                    description=str(ex),
                )
