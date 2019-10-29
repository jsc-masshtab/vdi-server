# -*- coding: utf-8 -*-
from abc import ABC
from tornado import websocket
import tornado
from tornado.escape import json_decode
import json

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import jwtauth

from pool.models import Pool, Vm
from vm.veil_client import VmHttpClient


@jwtauth
class PoolHandler(BaseHandler, ABC):
    async def get(self):
        # TODO: add user in get_pools execute
        pools = await Pool.get_pools()
        return self.finish(json.dumps(pools))


class PoolGetVm(BaseHandler, ABC):

    async def post(self):
        # TODO: есть подозрение, что иногда несмотря на отправленный запрос на просыпание VM - отправляется
        #  недостаточное количество данных для подключения тонкого клиента

        # user = request.user.username  # TODO: from where?
        # pool_id = int(request.path_params['pool_id'])

        pool_id = 71
        username = '11yo11a122b212'
        # username = None

        # Древние говорили, что сочитание pool id и имя пользователя должно быть обязательно уникальным
        # так как пользователь не может иметь больше одной машины в пуле
        user_vm = await Pool.get_user_pool(pool_id=pool_id, username=username)
        if not user_vm:
            return await self.finish(dict(host='',
                                          port=0, password='', message='Пул не найден'))
        [controller_ip, _, vm_id] = user_vm

        # Древние говорили, что если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
        if not vm_id:
            free_vm = await Pool.get_user_pool(pool_id=pool_id)
            if not free_vm:
                return await self.finish(dict(host='',
                                              port=0,
                                              password='',
                                              message='В пуле нет свободных машин'))

        # Древние говорили, что если свободная VM найдена, нужно закрепить ее за пользователем.
        if not vm_id and free_vm:
            print('free VM')
            [controller_ip, desktop_pool_type, vm_id] = free_vm
            await Vm.attach_vm_to_user(vm_id, username)

            # Логика древних:
            if desktop_pool_type == 'AUTOMATED':
                pool = await Pool.get_pool(pool_id)
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


class EchoWebSocket(websocket.WebSocketHandler, ABC):
    pass


class ActionOnVm(BaseHandler, ABC):

    async def post(self):
        # username = request.user.username
        # pool_id = int(request.path_params['pool_id'])
        # vm_action = request.path_params['action']
        # in pool find machine which belongs to user
        vm_action = 'reboot'
        username = 'yo11a2b212'
        pool_id = 59
        vms = await Vm.get_vm_id(pool_id=pool_id, username=username)

        if not vms:
            print('not vms?')
            return await self.finish({'error': 'Нет вм с указанным pool_id'})

        # determine vm controller ip by pool id
        controller_ip = await Pool.get_controller(pool_id)
        # print('controller_ip_', controller_ip)
        # do action

        client = VmHttpClient(controller_ip=controller_ip, vm_id=vms)
        await client.send_action(action=vm_action, body=self.request.body)
        return await self.finish({'error': 'null'})

