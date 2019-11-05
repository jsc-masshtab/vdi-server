# -*- coding: utf-8 -*-
from abc import ABC
import json

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import jwtauth, encode_jwt, refresh_access_token_with_expire_check as refresh_access_token
from pool.models import Pool, Vm
from auth.models import User
from vm.veil_client import VmHttpClient  # TODO: move to VM?


class AuthHandler(BaseHandler, ABC):
    async def post(self):
        if not self.args:
            # TODO: add proper exception
            return self.finish('Missing request body')
        if 'username' and 'password' not in self.args:
            # TODO: add proper exception
            return self.finish('Missing username and password')
        password_is_valid = await User.check_user(self.args['username'], self.args['password'])

        if not password_is_valid:
            # await User.set_password(self.args['username'], self.args['password'])  # сброс пароля
            return self.finish('invalid password')
        access_token = encode_jwt(self.args['username'])
        # TODO: если мы захотим хранить время, то придется делать запись в БД с обновлением
        return self.finish(access_token)


class RefreshAuthHandler(BaseHandler, ABC):
    # TODO: не окончательная версия. Нужно решить, делаем как в ECP разрешая обновлять только
    #  не истекшие времени или проверяем это по хранимому токену
    def post(self):
        try:
            token_info = refresh_access_token(self.request.headers)
        except:
            self._transforms = []
            self.set_status(401)
            return self.finish('Token has expired.')
        return self.finish(token_info)


@jwtauth
class PoolHandler(BaseHandler, ABC):
    # TODO: почему происходит 2 запроса, когда токен неправильный?
    async def get(self):
        pools = await Pool.get_pools()
        # TODO: json dumps потому что список, а не словарь. Нужно поменять формат обмена с клиентом,
        #  например на {'data' = pools} и заменить на tornado.escape.json_decode
        return self.finish(json.dumps(pools))


@jwtauth
class PoolGetVm(BaseHandler, ABC):

    async def post(self, pool_uid):
        # TODO: есть подозрение, что иногда несмотря на отправленный запрос на просыпание VM - отправляется
        #  недостаточное количество данных для подключения тонкого клиента
        username = self.get_current_user()

        # Древние говорили, что сочитание pool id и имя пользователя должно быть обязательно уникальным
        # так как пользователь не может иметь больше одной машины в пуле
        user_vm = await Pool.get_user_pool(pool_id=pool_uid, username=username)
        if not user_vm:
            return await self.finish(dict(host='',
                                          port=0, password='', message='Пул не найден'))
        [controller_ip, _, vm_id] = user_vm

        # Древние говорили, что если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
        if not vm_id:
            free_vm = await Pool.get_user_pool(pool_id=pool_uid)
            if not free_vm:
                return await self.finish(dict(host='',
                                              port=0,
                                              password='',
                                              message='В пуле нет свободных машин'))

        # Древние говорили, что если свободная VM найдена, нужно закрепить ее за пользователем.
        if not vm_id and free_vm:
            [controller_ip, desktop_pool_type, vm_id] = free_vm
            await Vm.attach_vm_to_user(vm_id, username)

            # Логика древних:
            if desktop_pool_type == 'AUTOMATED':
                pool = await Pool.get(pool_uid)
                await pool.expand_pool_if_requred()

        vm_client = VmHttpClient(controller_ip=controller_ip, vm_id=vm_id)
        info = await vm_client.info()

        # Проверяем включена ВМ и доступна ли для подключения.
        if Vm.ready_to_connect(**info):
            await vm_client.prepare()

        response = dict(host=controller_ip,
                        port=info['remote_access_port'],
                        password=info['graphics_password'])
        return await self.finish(response)


@jwtauth
class ActionOnVm(BaseHandler, ABC):

    async def post(self, pool_id, action):
        vm_action = action
        pool_id = int(pool_id)
        username = self.get_current_user()

        vms = await Vm.get_vm_id(pool_id=pool_id, username=username)
        if not vms:
            return await self.finish({'error': 'Нет вм с указанным pool_id'})

        controller_ip = await Pool.get_controller(pool_id)
        client = VmHttpClient(controller_ip=controller_ip, vm_id=vms)
        await client.send_action(action=vm_action, body=self.args)
        return await self.finish({'error': 'null'})

