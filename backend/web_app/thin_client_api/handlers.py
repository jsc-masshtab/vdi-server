# -*- coding: utf-8 -*-
from abc import ABC

from tornado import websocket
from aiohttp import client_exceptions
import asyncio
from common.settings import REDIS_PORT, REDIS_THIN_CLIENT_CHANNEL, REDIS_PASSWORD, REDIS_DB, VEIL_OPERATION_WAITING
from common.veil.veil_redis import request_to_execute_pool_task
from common.veil.veil_handlers import BaseHandler
from common.veil.veil_errors import ValidationError
from common.veil.auth.veil_jwt import jwtauth
from common.models.pool import Pool as PoolModel
from common.models.task import PoolTaskType
from veil_api_client import DomainTcpUsb

# from veil_api_client.base.api_objects.domain import DomainTcpUsb

from common.log.journal import system_logger
from common.languages import lang_init

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
        if not user:
            raise ValidationError(_('User {} not found.').format(user.username))
        pools = await user.pools
        response = {"data": pools}
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
            return await self.finish(response)
        user = await self.get_user_model_instance()
        if not user:
            response = {'errors': [{'message': _('User {} not found.'), 'code': '401'}]}
            return await self.log_finish(response)
        pool = await PoolModel.get(pool_id)
        if not pool:
            response = {'errors': [{'message': _('Pool not found.'), 'code': '404'}]}
            return await self.log_finish(response)
        pool_extended = False

        # Запрос на расширение пула
        if await pool.pool_type == PoolModel.PoolTypes.AUTOMATED:
            await request_to_execute_pool_task(pool.id_str, PoolTaskType.EXPANDING_POOL)
            pool_extended = True
        vm = await pool.get_vm(user_id=user.id)
        if not vm:
            # Если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
            vm = await pool.get_free_vm_v2()
            # Если свободная VM найдена, нужно закрепить ее за пользователем.
            if vm:
                await vm.add_user(user.id, creator='system')
                if await pool.pool_type == PoolModel.PoolTypes.AUTOMATED:
                    await request_to_execute_pool_task(pool.id_str, PoolTaskType.EXPANDING_POOL)
            elif pool_extended:
                response = {
                    'errors': [{'message': _('The pool doesn`t have free machines. Try again after 5 minutes.'),
                                'code': '002'}]}
                await request_to_execute_pool_task(pool.id_str, PoolTaskType.EXPANDING_POOL)
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

        try:
            # В данный момент подготовка есть только у автоматического пула, поэтому нужно включить удаленный доступ
            if await pool.pool_type == PoolModel.PoolTypes.STATIC and not veil_domain.remote_access:
                # Удаленный доступ выключен, нужно включить и ждать
                action_response = await veil_domain.enable_remote_access()
                if not action_response.success:
                    # Вернуть исключение?
                    raise ValueError(_('VeiL domain request error.'))
                if action_response.status_code == 200:
                    # Задача не встала в очередь, а выполнилась немедленно. Такого не должно быть.
                    raise ValueError(_('Task has`t been created.'))
                if action_response.status_code == 202:
                    # Была установлена задача. Необходимо дождаться ее выполнения.
                    # TODO: метод ожидания задачи
                    action_task = action_response.task
                    task_completed = False
                    while not task_completed:
                        await asyncio.sleep(VEIL_OPERATION_WAITING)
                        task_completed = await action_task.finished

                    # Если задача выполнена с ошибкой - прерываем выполнение
                    task_success = await action_task.success
                    if not task_success:
                        raise ValueError(
                            _('VM remote access task {} finished with error.').format(action_task.api_object_id))

                    # Обновляем параметры ВМ
                    await veil_domain.info()
        except ValueError:
            response = {'errors': [{'message': _('Can`t enable remote access. Check VeiL ECP.')}]}
            return await self.log_finish(response)

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
                vm_address = veil_domain.guest_agent.first_ipv4_ip
                if vm_address is None:
                    raise RuntimeError
                vm_port = 3389  # default rdp port

            except (RuntimeError, IndexError, KeyError):
                response = {'errors': [{'message': _('VM does not support RDP.')}]}
                return await self.log_finish(response)

        elif remote_protocol == PoolModel.PoolConnectionTypes.SPICE_DIRECT.name:
            # Нужен адрес сервера поэтому делаем запрос
            node_id = str(veil_domain.node['id'])
            node_info = await vm_controller.veil_client.node(node_id=node_id).info()
            vm_address = node_info.response[0].management_ip
            vm_port = info.data['real_remote_access_port']
        # PoolModel.PoolConnectionTypes.SPICE.name by default
        else:
            vm_address = vm_controller.address
            vm_port = veil_domain.remote_access_port

        response = {'data': dict(host=vm_address,
                                 port=vm_port,
                                 password=veil_domain.graphics_password,
                                 vm_verbose_name=veil_domain.verbose_name,
                                 vm_controller_address=vm_controller.address)
                    }

        return await self.log_finish(response)


@jwtauth
class VmAction(BaseHandler, ABC):
    """Пересылка действия над ВМ на ECP VeiL."""

    async def post(self, pool_id, action):
        try:
            force = self.args.get('force', False)
            user = await self.get_user_model_instance()
            vm = await BaseHandler.validate_and_get_vm(user, pool_id)
            # Все возможные проверки закончились - приступаем.
            await vm.action(action_name=action, force=force)
            response = {'data': 'success'}
        except AssertionError as vm_action_error:
            response = {'errors': [{'message': str(vm_action_error)}]}
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

    # todo: security problems. implement proper origin checking
    def check_origin(self, origin):
        return True
