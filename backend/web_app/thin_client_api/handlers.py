# -*- coding: utf-8 -*-
from abc import ABC

from tornado import websocket
from aiohttp import client_exceptions

from common.settings import REDIS_PORT, REDIS_THIN_CLIENT_CHANNEL, REDIS_PASSWORD, REDIS_DB
from common.veil.veil_redis import request_to_execute_pool_task, PoolTaskType
from common.veil.veil_handlers import BaseHandler
from common.veil.veil_errors import ValidationError
from common.veil.auth.veil_jwt import jwtauth
from common.models.pool import Pool as PoolModel

# from auth.models import User
# from vm import VmModel
# from pool.models import Pool, Vm
# from controller.models import Controller

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

    async def post(self, pool_id):  # remote_protocol: rdp/spice
        # Проверяем лимит виртуальных машин
        if PoolModel.thin_client_limit_exceeded():
            response = {'errors': [{'message': _('Thin client limit exceeded.'), 'code': '001'}]}
            return await self.finish(response)
        user = await self.get_user_model_instance()
        if not user:
            response = {'data': dict(host='', port=0, password='', message=_('User {} not found.'))}
            return await self.log_finish(response)
        pool = await PoolModel.get(pool_id)
        if not pool:
            response = {'data': dict(host='', port=0, password='', message=_('Pool not found.'))}
            return await self.log_finish(response)
        # Запрос на расширение пула
        if await pool.pool_type == PoolModel.PoolTypes.AUTOMATED:
            request_to_execute_pool_task(pool.id_str, PoolTaskType.EXPANDING.name)
        vm = await pool.get_vm(user_id=user.id)
        if not vm:
            # TODO: добавить третий метод в VM, который делает это
            # Если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
            vm = await pool.get_free_vm()
            # Если свободная VM найдена, нужно закрепить ее за пользователем.
            if vm:
                await vm.add_user(user.id, creator='system')
            else:
                response = {'data': dict(host='', port=0, password='', message=_('Pool doesnt have free machines'))}
                return await self.log_finish(response)

        # Дальше запросы начинают уходить на veil
        veil_domain = await vm.vm_client
        # Опытным путем установлено: если машина уже включена, то запрос может вернуться с 400.  Поэтому try
        # TODO: обработка новых исключений
        try:
            # TODO: use VM.prepare
            await vm.start()  # так предлагается использовать в дальнейшем
            await veil_domain.enable_remote_access()
            info_response = await veil_domain.info()
            info = info_response.value
        except client_exceptions.ServerDisconnectedError:
            response = {
                'data': dict(host='', port=0, password='', message=_('VM is unreachable on ECP Veil.'))}
            return await self.log_finish(response)

        # Определяем удаленный протокол. Если данные не были получены, то по умолчанию spice
        # try:
        #     remote_protocol = self.args['remote_protocol']
        # except KeyError:
        #     remote_protocol = 'spice'
        remote_protocol = self.args.get('remote_protocol', 'spice')

        # В зависимости от протокола определяем адрес машины
        # TODO: использовать hostname, который сейчас не задается
        if remote_protocol == 'rdp':
            try:
                vm_address = info['guest_utils']['ipv4'][0]
            except (IndexError, KeyError):
                response = {'data': dict(host='', port=0, password='',
                                              message=_('VM does not support RDP'))}
                return await self.log_finish(response)
        else:
            # spice by default
            vm_controller = await vm.controller
            vm_address = vm_controller.address

        response = {'data': dict(host=vm_address,
                                 port=veil_domain.remote_access_port,
                                 password=veil_domain.graphics_password,
                                 vm_verbose_name=veil_domain.verbose_name)
                    }

        return await self.log_finish(response)


@jwtauth
class VmAction(BaseHandler, ABC):
    """Пересылка действия над ВМ на ECP VeiL."""

    async def post(self, pool_id, action):
        try:
            force = self.args.get('force', False)
            user = await self.get_user_model_instance()
            if not user:
                raise ValidationError(_('User {} not found.').format(user.username))
            pool = await PoolModel.get(pool_id)
            if not pool:
                raise ValidationError(_('There is no pool with id: {}').format(pool_id))
            vm = await pool.get_vm(user_id=user.id)
            if not vm:
                raise ValidationError(_('User {} has no VM on pool {}').format(user.username, pool.id))
            # Все возможные проверки закончились - приступаем.
            await vm.action(action_name=action, force=force)
            response = {'data': 'success'}
        except AssertionError as vm_action_error:
            response = {'errors': [{'message': str(vm_action_error)}]}
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
