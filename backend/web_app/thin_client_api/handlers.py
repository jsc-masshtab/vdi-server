# -*- coding: utf-8 -*-
import asyncio
import json
import textwrap
from json.decoder import JSONDecodeError
from typing import Any

from aiohttp import client_exceptions

from sqlalchemy.sql import func

from tornado import httputil
from tornado.web import Application

from veil_api_client import DomainTcpUsb, VeilRetryConfiguration

from yaaredis.exceptions import LockError as RedisLockError

from common.languages import _local_
from common.log.journal import system_logger
from common.models.active_tk_connection import ActiveTkConnection, TkConnectionEvent
from common.models.auth import User
from common.models.pool import AutomatedPool, Pool as PoolM, RdsPool
from common.models.task import PoolTaskType, Task, TaskStatus
from common.models.tk_vm_connection import TkVmConnection
from common.models.vm import Vm
from common.settings import (
    INTERNAL_EVENTS_CHANNEL,
    REDIS_TEXT_MSG_CHANNEL,
    REDIS_THIN_CLIENT_CMD_CHANNEL,
    VEIL_OPERATION_WAITING,
    WS_MONITOR_CHANNEL_OUT
)
from common.subscription_sources import (
    EVENTS_THIN_CLIENT_SUBSCRIPTION, USERS_SUBSCRIPTION, WsMessageDirection, WsMessageType
)
from common.timezone import get_corresponding_linux_time_zone, get_corresponding_windows_time_zone
from common.veil.auth.veil_jwt import jwtauth, jwtauth_ws
from common.veil.veil_api import DomainOsType
from common.veil.veil_handlers import BaseHttpHandler, BaseWsHandler
from common.veil.veil_redis import (
    ThinClientCmd,
    publish_to_redis,
    redis_get_lock,
    redis_get_subscriber,
    request_to_execute_pool_task,
)


@jwtauth
class PoolHandler(BaseHttpHandler):
    """Возвращает все пулы пользователя."""

    async def get(self):
        user = await self.get_user_model_instance()
        pools = await user.pools
        response = {"data": pools}

        await system_logger.info(
            _local_("User {} requested pools data.").format(user.username),
            entity=user.entity,
            user=user.username,
        )
        return await self.log_finish(response)


@jwtauth
class PoolGetVm(BaseHttpHandler):
    """Получает конкретную ВМ пользователя."""

    def __init__(
        self,
        application: Application,
        request: httputil.HTTPServerRequest,
        **kwargs: Any
    ):
        super().__init__(application, request, **kwargs)
        self.user_id = None
        self.request_id = None
        self.client_time_zone = None
        self.client_os = None

    async def post(self, pool_id):
        remote_protocol = self.args.get("remote_protocol", PoolM.PoolConnectionTypes.SPICE.name)
        self.request_id = self.args.get("request_id")
        self.client_time_zone = self.args.get("time_zone")
        self.client_os = self.args.get("os")

        user = await self.get_user_model_instance()
        self.user_id = user.id
        pool = await PoolM.get(pool_id)
        # Some checks
        is_ok, response = await self._start_validate(pool, remote_protocol)
        if not is_ok:
            return await self.log_finish(response)

        pool_type = pool.pool_type
        expandable_pool = False  # В данный момент расширится может автоматический (гостевой пул)
        if pool_type == PoolM.PoolTypes.AUTOMATED or pool_type == PoolM.PoolTypes.GUEST:
            auto_pool = await AutomatedPool.get(pool.id)
            expandable_pool = True

        vm = await pool.get_vm(user_id=user.id)
        if not vm:  # ВМ для пользователя не присутствует
            await self._notify_vm_await_progress(progress=10, msg=_local_("Looking for machine."))

            if pool_type == PoolM.PoolTypes.RDS:
                # В случае RDS пула выдаем общий для всех RDS Сервер
                vms = await pool.get_vms()
                vm = vms[0]
                await vm.add_user(user.id, creator="system")
            else:
                # Если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
                # Critical section protected with redis lock https://aredis.readthedocs.io/en/latest/extra.html
                # Блокировка необходима для попытки избежать назначение одной ВМ нескольким пользователям
                # при одновременном запросе свободной ВМ от нескольких пользователей
                vms_global_lock = redis_get_lock(name="pool_vms_lock_" + pool.verbose_name, timeout=5,
                                                 blocking_timeout=10)
                lock_acquired = await vms_global_lock.acquire()
                if not lock_acquired:  # Не удалось получить лок
                    response = self.form_err_res(_local_("The pool is busy. Try again in 1 minute."), "006")
                    return await self.log_finish(response)

                try:
                    vm = await pool.get_free_vm_v2()
                    if vm:  # Machine found
                        await vm.add_user(user.id, creator="system")
                finally:
                    try:
                        await vms_global_lock.release()
                    except RedisLockError:  # Исключение будет, если лок уже был освобожден по таймауту
                        pass

                if vm:
                    await self._expand_pool_if_required(pool, expandable_pool)
                elif expandable_pool and not await auto_pool.check_if_total_size_reached():
                    await self._expand_pool_if_required(pool, expandable_pool)
                    response = self.form_err_res(
                        _local_("The pool doesn`t have free machines. Try again after 5 minutes."), "002")
                    return await self.log_finish(response)
                else:
                    response = self.form_err_res(_local_("The pool doesn`t have free machines."), "003")
                    return await self.log_finish(response)

        else:  # Даже если у пользователя есть ВМ, то попробовать расшириться все равно нужно
            await self._expand_pool_if_required(pool, expandable_pool)

        #  Включение ВМ и включение удаленного доступа, если спайс
        await self._notify_vm_await_progress(progress=30, msg=_local_("Machine is being prepared."))
        is_ok, response = await self._prepare_vm_if_required(vm, pool_type, remote_protocol)
        if not is_ok:
            return await self.log_finish(response)
        await system_logger.info(
            _local_("User {} connected to pool {}.").format(user.username, pool.verbose_name),
            entity=pool.entity,
            user=user.username,
        )

        # Актуализируем данные для подключения
        # Определяем адрес и порт в зависимости от протокола
        await self._notify_vm_await_progress(progress=50, msg=_local_("Connection data resolving (address/port)."))
        veil_domain = await vm.vm_client
        domain_info = await veil_domain.info()
        vm_controller = await vm.controller
        is_ok, response, vm_address, vm_port, vm_token = await self._get_conn_data(remote_protocol, vm_controller,
                                                                                   veil_domain, domain_info)
        if not is_ok:
            return await self.log_finish(response)

        permissions = await user.get_permissions()
        try:
            farm_list = await RdsPool.get_farm_list(pool.id, user.username) \
                if pool_type == PoolM.PoolTypes.RDS else []
        except (KeyError, IndexError, RuntimeError) as ex:
            response = self.form_err_res(_local_("Unable to get list of published applications. {}.").format(str(ex)))
            return await self.log_finish(response)
        response = {
            "data": dict(
                host=vm_address,
                port=vm_port,
                token=vm_token,
                password=veil_domain.graphics_password,
                vm_verbose_name=veil_domain.verbose_name,
                vm_controller_address=vm_controller.address,
                vm_id=str(vm.id),
                permissions=[permission.value for permission in permissions],
                farm_list=farm_list,
                pool_type=pool_type.name
            )
        }
        return await self.log_finish(response)

    async def _notify_vm_await_progress(self, progress: int, msg: str = None):
        """Отправить клиенту сообщение о прогрессе подготовки ВМ перед выдачей."""
        msg_dict = dict(
            msg_type=WsMessageType.DATA.value,
            resource=EVENTS_THIN_CLIENT_SUBSCRIPTION,
            event="vm_preparation_progress",
            user_id=str(self.user_id),
            progress=progress,
            msg=msg,
            request_id=int(self.request_id) if self.request_id else 0
        )

        await publish_to_redis(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))

    async def _get_conn_data(self, remote_protocol, vm_controller, veil_domain, domain_info):
        # Проверяем наличие клиента у контроллера
        veil_client = vm_controller.veil_client
        if not veil_client:
            response = self.form_err_res(_local_("The remote controller is unavailable."))
            return False, response, None, None, None

        if self._is_rdp(remote_protocol) or remote_protocol == PoolM.PoolConnectionTypes.X2GO.name:

            vm_port = 3389 if self._is_rdp(remote_protocol) else 22  # default port
            try:
                # Пробуем дождаться получения машиной адреса
                wait_timeout = 60
                vm_address = await asyncio.wait_for(self._get_ipv4_address(veil_domain), wait_timeout)
            except asyncio.TimeoutError:
                response = self.form_err_res(
                    _local_("The controller didn`t provide a VM address. Try again in 1 minute."), "005")
                return False, response, None, None, None

        elif remote_protocol == PoolM.PoolConnectionTypes.SPICE_DIRECT.name:
            # Нужен адрес сервера поэтому делаем запрос
            node_id = str(veil_domain.node["id"])
            node_info = await vm_controller.veil_client.node(node_id=node_id).info()
            vm_address = node_info.response[0].management_ip
            vm_port = domain_info.data["real_remote_access_port"]

        else:  # PoolM.PoolConnectionTypes.SPICE.name by default
            vm_address = vm_controller.address
            vm_port = veil_domain.remote_access_port

        #  Для подключения по спайсу через web нужен токен
        vm_token = None
        if self._is_spice(remote_protocol):
            spice = await veil_domain.spice_conn()
            if spice and spice.valid:
                vm_token = spice.token

        return True, None, vm_address, vm_port, vm_token

    async def _prepare_vm_if_required(self, vm, pool_type, remote_protocol):
        """Prepare VM if it's not ready. Return true if everything is ok."""
        try:
            # Запуск ВМ
            veil_domain = await vm.vm_client
            if not veil_domain:
                raise client_exceptions.ServerDisconnectedError()
            await veil_domain.info()
            if not veil_domain.powered:
                await vm.start()
            if self._is_spice(remote_protocol) and not veil_domain.remote_access:
                await veil_domain.enable_remote_access()

            # Time zone
            await self._set_time_zone_if_required(vm, veil_domain, pool_type)

        except client_exceptions.ServerDisconnectedError:
            response = self.form_err_res(_local_("VM is unreachable on ECP VeiL."), "004")
            return False, response
        except asyncio.TimeoutError:
            response = self.form_err_res(_local_("Controller did not reply. Check if it is available."), "005")
            return False, response

        return True, None

    async def _set_time_zone_if_required(self, vm, veil_domain, pool_type):

        # В случае RDS пула пробос зоны возможен на уровне сервера удаленных раб столов
        if pool_type != PoolM.PoolTypes.RDS and self.client_time_zone and self.client_os:
            try:
                await self._notify_vm_await_progress(progress=40, msg=_local_("Setting time zone."))

                # Дождаться активности qemu агента
                await asyncio.wait_for(vm.qemu_guest_agent_waiting(), VEIL_OPERATION_WAITING * 3)
                # Установка временной зоны.
                # Если ОС клиента и удаленной ВМ не совпадают, то находим соответствующее имя временной зоны
                vm_time_zone = None
                if self.client_os == DomainOsType.OTHER.value:
                    vm_time_zone = None
                elif self.client_os == veil_domain.os_type:
                    vm_time_zone = self.client_time_zone
                else:
                    if self.client_os == DomainOsType.LINUX.value and veil_domain.os_type == DomainOsType.WIN.value:
                        vm_time_zone = get_corresponding_windows_time_zone(self.client_time_zone)
                    elif self.client_os == DomainOsType.WIN.value and veil_domain.os_type == DomainOsType.LINUX.value:
                        vm_time_zone = get_corresponding_linux_time_zone(self.client_time_zone)

                # execute qemu agent command
                if vm_time_zone:
                    if veil_domain.os_type == DomainOsType.LINUX.value:
                        qemu_guest_command = {"path": "timedatectl",
                                              "arg": ["set-timezone", vm_time_zone],
                                              "capture-output": True}
                        response = await veil_domain.guest_command(qemu_cmd="guest-exec",
                                                                   f_args=qemu_guest_command)

                    elif veil_domain.os_type == DomainOsType.WIN.value:
                        qemu_guest_command = {"path": "tzutil.exe",
                                              "arg": ["/s", vm_time_zone],
                                              "capture-output": True}
                        response = await veil_domain.guest_command(qemu_cmd="guest-exec",
                                                                   f_args=qemu_guest_command)
                    else:  # Unreachable
                        return

                    if response.status_code == 400:
                        errors = response.data["errors"]
                        raise RuntimeError(errors)

                    stderr = response.data["guest-exec"].get("err-data")
                    if stderr:
                        stderr_stripped = stderr.strip().strip("\r\n")
                        if stderr_stripped:
                            raise RuntimeError(stderr_stripped)

            except (asyncio.TimeoutError, JSONDecodeError, KeyError, RuntimeError) as ex:
                # Если не удалось установить временную зону, это не причина не выдавать ВМ.
                # Лишь пишем предупреждение.
                await system_logger.warning(
                    message=_local_("Failed to set time zone for vm {}.").format(vm.verbose_name),
                    description=str(ex),
                )

    async def _get_ipv4_address(self, veil_domain):
        """Ожидаем получения адреса машиной."""
        attempt_number = 1
        while True:
            try:
                vm_address = veil_domain.first_ipv4
                if vm_address is None:
                    raise RuntimeError

                return vm_address

            except (RuntimeError, IndexError, KeyError):
                await asyncio.sleep(VEIL_OPERATION_WAITING)
                # Повторный запрос данных
                attempt_number += 1
                await self._notify_vm_await_progress(progress=70, msg=_local_(
                    "VM address resolving. Attempt number {}.").format(attempt_number))
                await veil_domain.info()

    @staticmethod
    def _is_spice(remote_protocol):
        return bool(remote_protocol == PoolM.PoolConnectionTypes.SPICE.name or  # noqa
                    remote_protocol == PoolM.PoolConnectionTypes.SPICE_DIRECT.name)  # noqa

    @staticmethod
    def _is_rdp(remote_protocol):
        return bool(remote_protocol == PoolM.PoolConnectionTypes.RDP.name or  # noqa
                    remote_protocol == PoolM.PoolConnectionTypes.NATIVE_RDP.name)  # noqa

    @staticmethod
    async def _start_validate(pool, remote_protocol):
        """Do some start validations."""
        # Проверяем лимит клиентов
        thin_client_limit_exceeded = await ActiveTkConnection.thin_client_limit_exceeded()
        if thin_client_limit_exceeded:
            response = PoolGetVm.form_err_res(_local_("Thin client limit exceeded."), "001")
            return False, response
        if not pool:
            response = PoolGetVm.form_err_res(_local_("Pool not found."), "404")
            return False, response

        # Protocol validation
        con_t = pool.connection_types
        bad_connection_type = remote_protocol not in PoolM.PoolConnectionTypes.values() or \
                              PoolM.PoolConnectionTypes[remote_protocol] not in con_t  # noqa: E127
        if bad_connection_type:
            response = PoolGetVm.form_err_res(
                _local_("The pool doesnt support connection type {}.").format(remote_protocol), "404")
            return False, response

        return True, None

    @staticmethod
    async def _expand_pool_if_required(pool_model, is_expandable_pool):
        """Только если расширение возможно и над пулом не выполняются другие задачи расширения."""  # noqa: E501
        if not pool_model or not is_expandable_pool:
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
class VmAction(BaseHttpHandler):
    """Пересылка действия над ВМ на ECP VeiL."""

    async def post(self, pool_id, action):

        user = await self.get_user_model_instance()
        vm = await self.validate_and_get_vm(user, pool_id)

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
            msg = _local_("User {} executed action {} on VM {}.")
        else:
            msg = _local_("User {} failed to execute action {} on VM {}.")
        await system_logger.info(
            msg.format(user.username, action, vm.verbose_name),
            entity=vm.entity,
            user=user.username,
        )

        return await self.log_finish(response)


@jwtauth
class AttachUsb(BaseHttpHandler):
    """Добавить usb tcp редирект девайс."""

    async def post(self, pool_id):

        host_address = self.validate_and_get_parameter("host_address")
        host_port = self.validate_and_get_parameter("host_port")

        user = await self.get_user_model_instance()
        vm = await self.validate_and_get_vm(user, pool_id)

        # attach request
        try:
            vm_controller = await vm.controller
            veil_client = vm_controller.veil_client.domain(
                domain_id=vm.id_str,
                retry_opts=VeilRetryConfiguration(num_of_attempts=0),
            )

            if not veil_client:
                raise AssertionError(_local_("VM has no api client."))
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
class DetachUsb(BaseHttpHandler):
    """Убрать usb tcp редирект девайс."""

    async def post(self, pool_id):

        usb_uuid = self.args.get("usb_uuid")
        remove_all = self.args.get("remove_all", False)

        user = await self.get_user_model_instance()
        vm = await self.validate_and_get_vm(user, pool_id)

        # detach request
        try:
            veil_client = await vm.vm_client
            if not veil_client:
                raise AssertionError(_local_("VM has no api client."))
            controller_response = await veil_client.detach_usb(
                action_type="tcp_usb_device", usb=usb_uuid, remove_all=remove_all
            )
            return await self.log_finish(controller_response.data)

        except AssertionError as error:
            response = {"errors": [{"message": str(error)}]}
        return await self.log_finish(response)


@jwtauth
class SendTextMsgHandler(BaseHttpHandler):
    """Текстовое сообщение от пользователя ТК.

    Пользователь ТК ничего не знает об админах, поэтому шлет сообщение всем текущим активным администраторам
    в канал REDIS_TEXT_MSG_CHANNEL
    """

    async def post(self):
        user = await self.get_user_model_instance()

        text_message = self.args.get("message")
        if not text_message:
            response = {"errors": [{"message": _local_("Message can not be empty.")}]}
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

            await publish_to_redis(REDIS_TEXT_MSG_CHANNEL, json.dumps(msg_data_dict))

            response = {"data": "success"}
            return await self.log_finish(response)

        except (KeyError, JSONDecodeError, TypeError) as ex:
            message = _local_("Wrong message format.") + str(ex)
            response = {"errors": [{"message": message}]}
            return await self.log_finish(response)


@jwtauth_ws
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

        try:
            # Сохраняем юзера с инфой
            tk_conn = await ActiveTkConnection.soft_create(
                conn_id=self.conn_id,
                is_conn_init_by_user=int(
                    self.get_query_argument(name="is_conn_init_by_user")
                ),
                user_id=self.user_id,
                veil_connect_version=self.get_query_argument("veil_connect_version"),
                tk_ip=self.remote_ip,
                tk_os=self.get_query_argument("tk_os"),
                mac_address=self.get_query_argument("mac_address", default=None),
                hostname=self.get_query_argument("hostname", default=None)
            )
            self.conn_id = tk_conn.id

            await self.send_msg(False, "Auth success")

        except Exception as ex:  # noqa
            await self.close_with_msg(True, str(ex), 4000)

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
                    if event_type == TkConnectionEvent.VM_CHANGED.value:  # юзер подключился/отключился от машины
                        # Блок кода оставлен для поддержки старых версий ТК
                        vm_id = recv_data_dict.get("vm_id")
                        conn_type = recv_data_dict.get("connection_type")
                        is_conn_secure = recv_data_dict.get("is_connection_secure")
                        if vm_id:
                            event_type = TkConnectionEvent.VM_CONNECTED.value
                        else:
                            vm_id = await tk_conn.get_last_connected_vm_id()
                            event_type = TkConnectionEvent.VM_DISCONNECTED.value

                        if vm_id:
                            await tk_conn.update_vm_data(event_type, vm_id, conn_type, is_conn_secure)

                    elif event_type == TkConnectionEvent.VM_CONNECTED.value or \
                        event_type == TkConnectionEvent.VM_DISCONNECTED.value:  # noqa

                        vm_id = recv_data_dict["vm_id"]
                        conn_type = recv_data_dict.get("connection_type")
                        is_conn_secure = recv_data_dict.get("is_connection_secure")
                        await tk_conn.update_vm_data(event_type, vm_id, conn_type, is_conn_secure)

                    elif event_type == TkConnectionEvent.VM_CONNECTION_ERROR.value:  # connection_type
                        await tk_conn.update_vm_data_on_error(recv_data_dict.get("vm_id"),
                                                              recv_data_dict.get("connection_type"),
                                                              recv_data_dict.get("conn_error_code"),
                                                              recv_data_dict.get("conn_error_str"))

                    elif event_type == TkConnectionEvent.USER_GUI.value:  # юзер нажал кнопку/кликнул
                        await tk_conn.update_last_interaction()

                    elif event_type == TkConnectionEvent.NETWORK_STATS.value:
                        await tk_conn.update_network_stats(**recv_data_dict)

        except (KeyError, ValueError, TypeError, JSONDecodeError) as ex:
            await self.send_msg(True, "Wrong msg format " + str(ex))
        except Exception as ex:
            await system_logger.debug(
                message=_local_("Ws: on_message: error"), description=(str(ex))
            )

    def on_close(self):
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
        # Обновляем дату последнего сообщения от ТК
        await ActiveTkConnection.update.values(data_received=func.now()).where(
            ActiveTkConnection.id == self.conn_id
        ).gino.status()

    async def _send_messages_co(self):
        """Отсылка сообщений на ТК. Сообщения достаются из редис каналов."""
        with redis_get_subscriber([INTERNAL_EVENTS_CHANNEL,
                                   WS_MONITOR_CHANNEL_OUT,
                                   REDIS_TEXT_MSG_CHANNEL]) as subscriber:
            while True:
                try:
                    redis_message = await subscriber.get_msg()

                    if redis_message["type"] == "message":
                        redis_message_data = redis_message["data"].decode()
                        redis_message_data_dict = json.loads(redis_message_data)

                        msg_type = redis_message_data_dict.get("msg_type")
                        if not msg_type:
                            continue

                        if msg_type == WsMessageType.DATA.value:
                            # Пересылаем сообщения об апдейте ВМ.
                            resource = redis_message_data_dict["resource"]
                            if resource == "/domains/":
                                vm_conn = await TkVmConnection.get_active_vm_conn(vm_id=redis_message_data_dict["id"],
                                                                                  tk_conn_id=self.conn_id)
                                if vm_conn:
                                    await self.write_msg(redis_message_data)
                            # Пересылем сообщения о событиях, связанных с ТК
                            elif resource == EVENTS_THIN_CLIENT_SUBSCRIPTION and \
                                redis_message_data_dict["user_id"] == str(self.user_id):  # noqa
                                await self.write_msg(redis_message_data)

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
                                await self.write_msg(redis_message_data)

                except asyncio.CancelledError:
                    break
                except (KeyError, ValueError, TypeError, JSONDecodeError) as ex:
                    await system_logger.debug(
                        message="Sending msg error in thin client ws handler.",
                        description=str(ex),
                    )

    async def _listen_for_cmd(self):
        """Команды от админа."""
        with redis_get_subscriber([REDIS_THIN_CLIENT_CMD_CHANNEL]) as subscriber:
            while True:
                try:
                    redis_message = await subscriber.get_msg()

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
                                # Отсылаем клиенту команду. По ней он отключится от машины и разлогинится
                                await self.close_with_msg(False, "Disconnect requested", 2000,
                                                          cmd=ThinClientCmd.DISCONNECT.name)

                except asyncio.CancelledError:
                    break
                except (KeyError, ValueError, TypeError, JSONDecodeError) as ex:
                    await system_logger.debug(
                        message="Thin client ws listening commands error.",
                        description=str(ex),
                    )


@jwtauth
class GenerateUserQrCodeHandler(BaseHttpHandler):
    """Генерация данных для qr."""

    async def post(self):
        user = await self.get_user_model_instance()
        data_dict = await user.generate_qr(creator=user.username)

        response = {
            "data": dict(qr_uri=data_dict["qr_uri"], secret=data_dict["secret"])
        }

        return await self.log_finish(response)


@jwtauth
class GetUserDataHandler(BaseHttpHandler):

    async def get(self):
        user = await self.get_user_model_instance()

        response = {
            "data": dict(user=dict(two_factor=user.two_factor))
        }
        return await self.log_finish(response)


@jwtauth
class UpdateUserDataHandler(BaseHttpHandler):

    async def post(self):

        try:
            user = await self.get_user_model_instance()  # Проверка что пользователь обновляет свои данные, а не чужие

            two_factor = self.validate_and_get_parameter("two_factor")

            await User.soft_update(id=user.id, creator=user.username, two_factor=two_factor)
            response = {
                "data": dict(ok=True,
                             user=dict(two_factor=two_factor))
            }
        except (AssertionError, TypeError) as error:
            response = {"errors": [{"message": str(error)}]}

        return await self.log_finish(response)


@jwtauth
class VmDataHandler(BaseHttpHandler):
    """Возвращает все пулы пользователя."""

    async def get(self, vm_id):
        vm = await Vm.get(vm_id)

        if not vm:
            response = self.form_err_res(_local_("VM {} is not registered in VDI broker.").format(vm_id))
            return await self.log_finish(response)

        vm_controller = await vm.controller
        http_vac_client = vm_controller.veil_client.domain(domain_id=vm.id_str)
        domain_info = await http_vac_client.info()

        response_data = domain_info.data
        response_data["controller_address"] = vm_controller.address
        response = {
            "data": response_data
        }

        return await self.log_finish(response)
