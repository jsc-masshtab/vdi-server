# -*- coding: utf-8 -*-
from abc import ABC
from typing import Any
from tornado.web import Application
from tornado import httputil
import json
from json.decoder import JSONDecodeError

from tornado import websocket
from aiohttp import client_exceptions
import asyncio
from common.settings import REDIS_PORT, REDIS_THIN_CLIENT_CHANNEL, REDIS_PASSWORD, REDIS_DB,\
    REDIS_THIN_CLIENT_CMD_CHANNEL
from common.veil.veil_redis import request_to_execute_pool_task, ThinClientCmd
from common.veil.veil_handlers import BaseHandler
from common.veil.auth.veil_jwt import jwtauth, decode_jwt

from sqlalchemy.sql import func
from common.models.pool import Pool as PoolModel, AutomatedPool
from common.models.task import PoolTaskType, TaskStatus, Task
from common.models.auth import UserJwtInfo
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User

from veil_api_client import DomainTcpUsb

# from veil_api_client.base.api_objects.domain import DomainTcpUsb

from common.log.journal import system_logger
from common.languages import lang_init


from common.settings import JWT_OPTIONS

from common.veil.veil_redis import WS_MONITOR_CHANNEL_OUT, REDIS_CLIENT, a_redis_get_message


_ = lang_init()


@jwtauth
class RedisInfoHandler(BaseHandler, ABC):
    """Данные для подключения тонких клиентов к Redis."""

    async def get(self):
        """
        {
            "data": {
                "port": 6379,
                "password": "veil",
                "channel": "TC_CHANNEL"
                "db": 0:
            }
        }
        """
        redis_info = dict(port=REDIS_PORT, channel=REDIS_THIN_CLIENT_CHANNEL, password=REDIS_PASSWORD, db=REDIS_DB)
        response = dict(data=redis_info)
        return self.finish(response)


@jwtauth
class PoolHandler(BaseHandler, ABC):
    """Возвращает все пулы пользователя."""

    async def get(self):
        user = await self.get_user_model_instance()
        pools = await user.pools
        response = {"data": pools}

        await system_logger.info(_('User {} requested pools data.').format(user.username),
                                 entity=user.entity, user=user.username)
        return await self.log_finish(response)


@jwtauth
class PoolGetVm(BaseHandler, ABC):
    """Получает конкретную ВМ пользователя."""

    async def post(self, pool_id):
        # Определяем удаленный протокол. Если данные не были получены, то по умолчанию spice
        remote_protocol = self.args.get('remote_protocol', PoolModel.PoolConnectionTypes.SPICE.name)
        remote_protocol = remote_protocol.upper()  # ТК присылвет в нижнем регистре для совместимости со
        # старыми версиями vdi сервера

        # Проверяем лимит виртуальных машин
        if PoolModel.thin_client_limit_exceeded():
            response = {'errors': [{'message': _('Thin client limit exceeded.'), 'code': '001'}]}
            return await self.log_finish(response)

        user = await self.get_user_model_instance()
        pool = await PoolModel.get(pool_id)
        if not pool:
            response = {'errors': [{'message': _('Pool not found.'), 'code': '404'}]}
            return await self.log_finish(response)
        pool_extended = False

        # Проверяем разрешен ли присланный remote_protocol для данного пула
        if PoolModel.PoolConnectionTypes[remote_protocol] not in pool.connection_types:
            response = {'errors': [{'message': _('The pool doesnt support connection type {}.').format(remote_protocol),
                                    'code': '404'}]}
            return await self.log_finish(response)

        # Запрос на расширение пула
        if await pool.pool_type == PoolModel.PoolTypes.AUTOMATED:
            await self._send_cmd_to_expand_pool(pool)
            pool_extended = True
        vm = await pool.get_vm(user_id=user.id)
        if not vm:
            # Если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
            vm = await pool.get_free_vm_v2()
            # Если свободная VM найдена, нужно закрепить ее за пользователем.
            if vm:
                await vm.add_user(user.id, creator='system')
                if await pool.pool_type == PoolModel.PoolTypes.AUTOMATED:
                    await self._send_cmd_to_expand_pool(pool)
            elif pool_extended:
                response = {
                    'errors': [{'message': _('The pool doesn`t have free machines. Try again after 5 minutes.'),
                                'code': '002'}]}
                await self._send_cmd_to_expand_pool(pool)
                return await self.log_finish(response)
            else:
                response = {'errors': [{'message': _('The pool doesn`t have free machines.'),
                                        'code': '003'}]}
                return await self.log_finish(response)

        # TODO: обработка новых исключений
        # Подготовка ВМ теперь происходит при создании и расширении пула. Тут только влючение ВМ.
        try:
            # Дальше запросы начинают уходить на veil
            veil_domain = await vm.vm_client
            if not veil_domain:
                raise client_exceptions.ServerDisconnectedError()
            await veil_domain.info()
            if not veil_domain.powered:
                await vm.start()

        except client_exceptions.ServerDisconnectedError:
            response = {'errors': [{'message': _('VM is unreachable on ECP Veil.'),
                                    'code': '004'}]}
            return await self.log_finish(response)
        # Актуализируем данные для подключения
        info = await veil_domain.info()

        await system_logger.info(_('User {} connected to pool {}.').format(user.username, pool.verbose_name),
                                 entity=pool.entity, user=user.username)
        await system_logger.info(_('User {} connected to VM {}.').format(user.username, vm.verbose_name),
                                 entity=vm.entity, user=user.username)
        # TODO: использовать veil_domain.hostname вместо IP

        # Определяем адресс и порт в зависимости от протокола
        vm_controller = await vm.controller
        # Проверяем наличие клиента у контроллера
        veil_client = vm_controller.veil_client
        if not veil_client:
            response = {'errors': [{'message': _('The remote controller is unavailable.')}]}
            return await self.log_finish(response)

        if remote_protocol == PoolModel.PoolConnectionTypes.RDP.name or \
                remote_protocol == PoolModel.PoolConnectionTypes.NATIVE_RDP.name:
            try:
                vm_address = veil_domain.first_ipv4
                if vm_address is None:
                    raise RuntimeError
                vm_port = 3389  # default rdp port

            except (RuntimeError, IndexError, KeyError):
                # TODO: записать в журнал какой ответ пришел от вейла
                response = {'errors': [{'message': _('VM does not support RDP. The controller didn`t provide a VM address.')}]}
                return await self.log_finish(response)

        elif remote_protocol == PoolModel.PoolConnectionTypes.SPICE_DIRECT.name:
            # Нужен адрес сервера поэтому делаем запрос
            node_id = str(veil_domain.node['id'])
            node_info = await vm_controller.veil_client.node(node_id=node_id).info()
            vm_address = node_info.response[0].management_ip
            vm_port = info.data['real_remote_access_port']

        else:  # PoolModel.PoolConnectionTypes.SPICE.name by default
            vm_address = vm_controller.address
            vm_port = veil_domain.remote_access_port

        response = {'data': dict(host=vm_address,
                                 port=vm_port,
                                 password=veil_domain.graphics_password,
                                 vm_verbose_name=veil_domain.verbose_name,
                                 vm_controller_address=vm_controller.address,
                                 vm_id=str(vm.id))
                    }
        return await self.log_finish(response)

    async def _send_cmd_to_expand_pool(self, pool_model):
        """Запускаем задачу только если расширение возможно и над пулом не выполняютя другие задачи"""

        if not pool_model:
            return
        # 1) is max reached
        autopool = await AutomatedPool.get(pool_model.id)
        total_size_reached = await autopool.check_if_total_size_reached()
        # 2) is not enough free vms
        is_not_enough_free_vms = await autopool.check_if_not_enough_free_vms()
        # 3) other tasks
        tasks = await Task.get_tasks_associated_with_entity(pool_model.id, TaskStatus.IN_PROGRESS)

        if not total_size_reached and not tasks and is_not_enough_free_vms:
            await request_to_execute_pool_task(pool_model.id, PoolTaskType.POOL_EXPAND)


@jwtauth
class VmAction(BaseHandler, ABC):
    """Пересылка действия над ВМ на ECP VeiL."""

    async def post(self, pool_id, action):

        user = await self.get_user_model_instance()
        vm = await BaseHandler.validate_and_get_vm(user, pool_id)

        try:
            force = self.args.get('force', False)
            # Все возможные проверки закончились - приступаем.
            is_action_successful = await vm.action(action_name=action, force=force)
            response = {'data': 'success'}
        except AssertionError as vm_action_error:
            response = {'errors': [{'message': str(vm_action_error)}]}
            is_action_successful = False

        # log action
        if is_action_successful:
            msg = _('User {} executed action {} on VM {}.')
        else:
            msg = _('User {} failed to execute action {} on VM {}.')
        await system_logger.info(msg.format(user.username, action, vm.verbose_name),
                                 entity=vm.entity, user=user.username)

        return await self.log_finish(response)


@jwtauth
class AttachUsb(BaseHandler, ABC):
    """Добавить usb tcp редирект девайс"""

    async def post(self, pool_id):

        host_address = self.validate_and_get_parameter('host_address')
        host_port = self.validate_and_get_parameter('host_port')

        user = await self.get_user_model_instance()
        vm = await BaseHandler.validate_and_get_vm(user, pool_id)

        # attach request
        try:
            veil_client = await vm.vm_client
            if not veil_client:
                raise AssertionError(_('VM has no api client.'))
            domain_tcp_usb_params = DomainTcpUsb(host=host_address, service=host_port)
            controller_response = await veil_client.attach_usb(action_type='tcp_usb_device',
                                                               tcp_usb=domain_tcp_usb_params, no_task=True)
            return await self.log_finish(controller_response.data)

        except AssertionError as error:
            response = {'errors': [{'message': str(error)}]}
        return await self.log_finish(response)


@jwtauth
class DetachUsb(BaseHandler, ABC):
    """Убрать usb tcp редирект девайс"""

    async def post(self, pool_id):

        usb_uuid = self.args.get('usb_uuid')
        remove_all = self.args.get('remove_all', False)

        user = await self.get_user_model_instance()
        vm = await BaseHandler.validate_and_get_vm(user, pool_id)

        # detach request
        try:
            veil_client = await vm.vm_client
            if not veil_client:
                raise AssertionError(_('VM has no api client.'))
            controller_response = await veil_client.detach_usb(action_type='tcp_usb_device',
                                                               usb=usb_uuid, remove_all=remove_all)
            return await self.log_finish(controller_response.data)

        except AssertionError as error:
            response = {'errors': [{'message': str(error)}]}
        return await self.log_finish(response)


class ThinClientWsHandler(websocket.WebSocketHandler):  # noqa
    # TODO: 1 модуль для вебсокетов
    # сделать модуль ws_api, где бы все связанное с вебсокетами хранилось
    # главное короч чтоб для тк внешне ничо не изменилось
    # url чуть разный, но в список ws урлов можно несколько добавиьт
    # def __init__(self, application: Application, request: httputil.HTTPServerRequest, **kwargs: Any):
    #     websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
    #     print('init')

    def __init__(self, application: Application, request: httputil.HTTPServerRequest, **kwargs: Any):
        websocket.WebSocketHandler.__init__(self, application, request, **kwargs)

        self.conn_id = None
        self._send_messages_task = None
        self._listen_for_cmd_task = None

    def check_origin(self, origin):
        return origin == 'veil_connect_trusted_origin'

    async def open(self):
        # print('on open ', self.request.remote_ip, flush=True)
        loop = asyncio.get_event_loop()
        self._send_messages_task = loop.create_task(self._send_messages_co())
        self._listen_for_cmd_task = loop.create_task(self._listen_for_cmd())

    async def on_message(self, message):
        # print('!!!message: ', message, flush=True)

        # parse msg
        try:
            recv_data_dict = json.loads(message)
            msg_type = recv_data_dict['msg_type']
        except (KeyError, JSONDecodeError) as ex:
            response = {'msg_type': 'control', 'error': True, 'msg': 'Wrong msg format ' + str(ex)}
            await self.write_message(json.dumps(response))
            return

        # Сообщение AUTH. собщение авторизации со стартовой инфой с ТК
        if msg_type == 'AUTH':
            try:
                # Проверяем токен. Рвем соединение если токен левый
                token = recv_data_dict['token']
                jwt_info = await UserJwtInfo.query.where(UserJwtInfo.token == token).gino.first()
                if not jwt_info:
                    raise AssertionError('Auth failed')

                # Извлекаем инфу из токена
                JWT_OPTIONS['verify_exp'] = False
                payload = decode_jwt(token, JWT_OPTIONS)
                user_name = payload['username']

                # Фиксируем  данные известные на стороне сервера
                user_id = await User.get_id(user_name)
                if not user_id:
                    raise AssertionError(_('User {} not found.').format(user_name))

                # Сохраняем юзера с инфой
                tk_conn = await ActiveTkConnection.soft_create(
                    conn_id=self.conn_id, user_id=user_id,
                    veil_connect_version=recv_data_dict['veil_connect_version'],
                    vm_id=recv_data_dict['vm_id'],
                    tk_ip=self.request.remote_ip,
                    tk_os=recv_data_dict['tk_os'])
                self.conn_id = tk_conn.id

                response = {'msg_type': 'control', 'error': False, 'msg': 'Auth success'}
                await self._write_msg(json.dumps(response))

            except (KeyError, TypeError, JSONDecodeError, AssertionError) as ex:
                response = {'msg_type': 'control', 'error': True, 'msg': str(ex)}
                await self._write_msg(json.dumps(response))
                self.close()

        # Сообщения UPDATED
        elif msg_type == 'UPDATED':
            await self._close_if_not_verified()

            try:
                event_type = recv_data_dict['event']

                if event_type == 'vm_changed':  # юзер подключился/отключился от машины
                    await ActiveTkConnection.update_vm_id(self.conn_id, recv_data_dict['vm_id'])
                elif event_type == 'user_gui':  # юзер нажал кнопку/кликнул
                    await ActiveTkConnection.update_last_interaction(self.conn_id)
            except KeyError:
                pass

    def on_close(self):
        # print("!!!WebSocket closed", flush=True)
        loop = asyncio.get_event_loop()
        loop.create_task(self.on_async_close())

        # stop tasks
        self._send_messages_task.cancel()
        self._listen_for_cmd_task.cancel()

    async def on_async_close(self):
        tk_conn = await ActiveTkConnection.get(self.conn_id)
        if tk_conn:
            await tk_conn.deactivate()

    async def on_pong(self, data: bytes) -> None:
        # print("WebSocket on_pong", flush=True)

        await self._close_if_not_verified()

        # Обновляем дату последнего сообщения от ТК
        await ActiveTkConnection.update.values(data_received=func.now()).where(
            ActiveTkConnection.id == self.conn_id).gino.status()

    async def _close_if_not_verified(self):
        if self.conn_id is None:
            response = {'msg_type': 'control', 'error': False, 'msg': 'Auth required'}
            await self._write_msg(json.dumps(response))
            self.close()

    async def _send_messages_co(self):
        """Пересылвем сообщения об аптейте ВМ"""

        redis_subscriber = REDIS_CLIENT.pubsub()
        redis_subscriber.subscribe(WS_MONITOR_CHANNEL_OUT)

        while True:
            try:
                redis_message = await a_redis_get_message(redis_subscriber)

                if redis_message['type'] == 'message':
                    redis_message_data = redis_message['data'].decode()
                    redis_message_data_dict = json.loads(redis_message_data)

                    if redis_message_data_dict['resource'] == '/domains/':

                        vm_id = await ActiveTkConnection.get_vm_id(self.conn_id)
                        if redis_message_data_dict['id'] == str(vm_id):
                            await self._write_msg(redis_message_data)

            except asyncio.CancelledError:
                break
            except Exception as ex:
                await system_logger.debug(str(ex))

    async def _listen_for_cmd(self):
        """Команды от админа"""
        redis_subscriber = REDIS_CLIENT.pubsub()
        redis_subscriber.subscribe(REDIS_THIN_CLIENT_CMD_CHANNEL)

        while True:
            try:
                redis_message = await a_redis_get_message(redis_subscriber)

                if redis_message['type'] == 'message':
                    redis_message_data = redis_message['data'].decode()
                    redis_message_data_dict = json.loads(redis_message_data)

                    if redis_message_data_dict['command'] == ThinClientCmd.DISCONNECT.name:
                        conn_id = redis_message_data_dict['conn_id']

                        # От админа приходит команда с id соединения, которое надо закрыть
                        if self.conn_id and conn_id == str(self.conn_id):
                            # Отсылаем клиенту команду. По ней он отключится от машины
                            response = {'msg_type': 'control', 'cmd': ThinClientCmd.DISCONNECT.name,
                                        'error': False, 'msg': 'Disconnect requested'}
                            await self._write_msg(json.dumps(response))
                            self.close()

            except asyncio.CancelledError:
                break
            except Exception as ex:
                await system_logger.debug(str(ex))

    async def _write_msg(self, msg):
        try:
            await self.write_message(msg)
        except websocket.WebSocketError:
            await system_logger.debug(_('Write error.'))
