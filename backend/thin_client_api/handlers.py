# -*- coding: utf-8 -*-
from abc import ABC
import asyncio

from tornado import websocket

from common.utils import cancel_async_task
from common.veil_handlers import BaseHandler
from common.veil_errors import HttpError, ValidationError, NotFound

from settings import REDIS_PORT, REDIS_THIN_CLIENT_CHANNEL, REDIS_PASSWORD, REDIS_DB
from auth.utils.veil_jwt import jwtauth
from auth.models import User
from pool.models import Pool, Vm, AutomatedPool
from vm.veil_client import VmHttpClient  # TODO: move to VM?
from pool.pool_task_manager import pool_task_manager
from controller.models import Controller

from languages import lang_init


_ = lang_init()


@jwtauth
class RedisInfoHandler(BaseHandler, ABC):
    async def get(self):
        """
        Данные для подключения тонких клиентов к Redis
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

    async def get(self):
        """Возвращает все пулы пользователя"""

        username = self.get_current_user()
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        pools = await user.pools
        response = {"data": pools}
        return self.log_finish(response)


@jwtauth
class PoolGetVm(BaseHandler, ABC):

    async def post(self, pool_id):  # remote_protocol: rdp/spice
        # Проверяем лимит виртуальных машин
        if Pool.thin_client_limit_exceeded():
            response = {'errors': [{'message': _('Thin client limit exceeded.'), 'code': '001'}]}
            return await self.finish(response)

        # Сочитание pool id и username уникальное, т.к. пользователь не может иметь больше одной машины в пуле

        username = self.get_current_user()
        user_id = await User.get_id(username)
        pool = await Pool.get(pool_id)
        if not pool:
            response = {'data': dict(host='', port=0, password='', message=_('Pool not found.'))}
            return await self.log_finish(response)

        controller_ip = await Controller.select('address').where(Controller.id == pool.controller).gino.scalar()
        # TODO: отказаться от vm_id
        # Проверяем права пользователя на доступ к пулу:
        # TODO: после перевода VM на новую модель разрешений - необходимо будет учесть наличие роли
        assigned_users = await pool.assigned_users
        assigned_users_list = [user.username for user in assigned_users]
        if username not in assigned_users_list:
            response = {
                'data': dict(host='', port=0, password='', message=_('User does not have permission to use pool.'))}
            return await self.log_finish(response)

        # Ищем VM закрепленную за пользователем:
        vm_id = await Vm.get_vm_id(pool_id, user_id)
        if not vm_id:
            # TODO: добавить третий метод в VM, который делает это
            # Если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
            # vm_id = await pool.get_free_vm_id()
            vm = await pool.get_free_vm()

            # Если свободная VM найдена, нужно закрепить ее за пользователем.
            if vm:
                vm_id = vm.id
                await vm.add_user(user_id)
                # await vm.attach_to_user(user_id)

        # В отдельной корутине запускаем расширение пула
        if await pool.pool_type == Pool.PoolTypes.AUTOMATED:
            pool = await AutomatedPool.get(pool_id)
            pool_lock = pool_task_manager.get_pool_lock(pool_id)
            template_lock = pool_task_manager.get_template_lock(str(pool.template_id))
            # Проверяем залочены ли локи. Если залочены, то ничего не делаем, так как любые другие действия с
            # пулом требующие блокировки - в приоретете.
            if not pool_lock.lock.locked() and not template_lock.lock.locked():
                async with pool_lock.lock:
                    native_loop = asyncio.get_event_loop()
                    await cancel_async_task(pool_lock.expand_pool_task)
                    pool_lock.expand_pool_task = native_loop.create_task(pool.expand_pool())

        if not vm_id:
            response = {'data': dict(host='', port=0, password='', message=_('Pool has not free machines'))}
            return await self.log_finish(response)

        # Дальше запросы начинают уходить на veil
        #  Опытным путем было выяснено, что vm info содержит remote_access_port None, пока не врубишь
        # удаленный доступ. Поэтому врубаем его без проверки, чтоб не запрашивать инфу 2 раза
        vm_client = await VmHttpClient.create(controller_ip=str(controller_ip), vm_id=str(vm_id))

        # Опытным путем установлено: если машина уже включена, то запрос может вернуться с 400.  Поэтому try
        try:
            await vm_client.prepare()
        except NotFound:
            response = {
                'data': dict(host='', port=0, password='', message=_('VM is unreachable on ECP Veil.'))}
            return await self.log_finish(response)
        except HttpError as err_response_body:
            detail = vm_client.parse_veil_errors('', err_response_body)
            if (isinstance(detail, tuple) and 're not consolidated vdisks' in detail[0]) or 're not consolidated vdisks' in detail:  # noqa
                response = {
                    'data': dict(host='', port=0, password='', message=_('VM is unreachable on ECP Veil.'))}
                return await self.log_finish(response)
        try:
            info = await vm_client.info()
        except HttpError:
            response = {
                'data': dict(host='', port=0, password='', message=_('VM is unreachable on ECP Veil.'))}
            return await self.log_finish(response)

        # Определяем удаленный протокол. Если данные не были получены, то по умолчанию spice
        try:
            remote_protocol = self.args['remote_protocol']
        except KeyError:
            remote_protocol = 'spice'

        # В зависимости от протокола определяем адрес машины
        if remote_protocol == 'rdp':
            try:
                vm_address = info['guest_utils']['ipv4'][0]
            except (IndexError, KeyError):
                response = {'data': dict(host='', port=0, password='',
                                              message=_('VM does not support RDP'))}
                return await self.log_finish(response)
        else:  # spice by default
            vm_address = str(controller_ip)

        response = {'data': dict(host=vm_address,
                                 port=info['remote_access_port'],
                                 password=info['graphics_password'],
                                 vm_verbose_name=info['verbose_name'])
                    }

        return await self.log_finish(response)


@jwtauth
class VmAction(BaseHandler, ABC):

    async def post(self, pool_id, action):
        try:
            username = self.get_current_user()
            user_id = await User.get_id(username)
            if not user_id:
                raise ValidationError(_('User {} not found.').format(username))
            pool = await Pool.get(pool_id)
            if not pool:
                raise ValidationError(_('There is no pool with id: {}').format(pool_id))
            # TODO: проверить права доступа пользователя к VM через assigned_users у Pool
            vm_id = await Vm.get_vm_id(pool_id=pool_id, user_id=user_id)
            if not vm_id:
                raise ValidationError(_('User {} has no VM on pool {}').format(username, pool_id))

            controller_ip = await Pool.get_controller_ip(pool_id)
            client = await VmHttpClient.create(controller_ip=controller_ip, vm_id=vm_id)
            await client.send_action(action=action, body=self.args)
            response = {'data': 'success'}
        except (AssertionError, HttpError) as vm_action_error:
            response = {'errors': [{'message': str(vm_action_error)}]}
        return self.log_finish(response)


class ThinClientWsHandler(websocket.WebSocketHandler):  # noqa
    # TODO: есть стойкое ощущение, что не нужен этот блок и лучше таймаутом ходить и получать статус сервера
    # def __init__(self, application: Application, request: httputil.HTTPServerRequest, **kwargs: Any):
    #     websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
    #     print('init')

    # todo: security problems. implement proper origin checking
    def check_origin(self, origin):
        return True
