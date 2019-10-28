# -*- coding: utf-8 -*-
from abc import ABC
from tornado import gen
from tornado import websocket
import tornado

import json  # TODO: remove me

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import jwtauth

from pool.models import Pool, Vm
from pool.schema import DesktopPoolType
from vm.veil_client import VmHttpClient


@jwtauth
class PoolHandler(BaseHandler, ABC):
    @gen.coroutine
    def get(self):
        # TODO: add user
        pools = yield Pool.get_pools()
        return self.finish(json.dumps(pools))  # TODO: because Tornado don't recomends to send list. Think about it.


class PoolGetVm(BaseHandler, ABC):
    # TODO: from where user?

    @gen.coroutine
    def post(self):
        # TODO: есть подозрение, что иногда несмотря на отправленный запрос на просыпание VM - отправляется недостаточное количество данных для подключения тонкого клиента
        yoba_params = ('remote_access_port', 'graphics_password', 'remote_access', 'remote_access_allow_all', 'status')
        # user = request.user.username  # TODO: from where?
        # pool_id = int(request.path_params['pool_id'])

        pool_id = 59
        username = 'yo11a2b212'
        # username = None

        # ниже окончательный код

        # Древние говорили, что сочитание pool id и имя пользователя должно быть обязательно уникальным
        # так как пользователь не может иметь больше одной машины в пуле
        pools = yield Pool.get_user_pool(pool_id=pool_id, username=username)
        if not pools:
            return self.finish(dict(host='',
                                    port=0, password='', message='Пул не найден'))

        [controller_ip, desktop_pool_type, vm_id] = pools
        # TODO: поменять логику запроса?
        # TODO: разнести на 2 метода?
        if vm_id:
            vm_client = VmHttpClient(controller_ip=controller_ip, vm_id=vm_id)
            info = yield vm_client.info()

            # Проверяем включена ВМ и доступна ли для подключения.
            if Vm.ready_to_connect(**info):
                yield vm_client.prepare()

            response = dict(host=controller_ip,
                            port=info['remote_access_port'],
                            password=info['graphics_password'])
            return self.finish(response)

        # Древние говорили, что если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
        print('Search free VM')
        free_vm = yield Pool.get_user_pool(pool_id=pool_id)
        if not free_vm:
            return self.finish(dict(host='',
                                    port=0,
                                    password='',
                                    message='В пуле нет свободных машин'))

        print('Free VM founded!')
        # Древние говорили, что если свободная VM найдена, нужно закрепить ее за пользователем.
        [_, _, vm_id] = free_vm

        print('vm id is {}'.format(vm_id))

        yield Vm.attach_vm_to_user(vm_id, username)

        # Логика древних:  # TODO: не забыть переписать
        # if desktop_pool_type == DesktopPoolType.AUTOMATED.name:
        #     pool = yield AutomatedPoolManager.get_pool(pool_id)
        #     yield pool.expand_pool_if_requred()

        # TODO: явное дублирование кода
        print('Get free VM info')
        vm_client = VmHttpClient(controller_ip=controller_ip, vm_id=vm_id)
        info = yield vm_client.info()

        print('Prepare free VM')
        yield vm_client.prepare()
        print('Return free VM connection data')

        response = dict(host=controller_ip,
                        port=info['remote_access_port'],
                        password=info['graphics_password'])
        return self.finish(response)


class EchoWebSocket(websocket.WebSocketHandler, ABC):
    pass


class ActionOnVm(BaseHandler, ABC):

    @gen.coroutine
    def post(self):
        print('do_action_on_vm')
        # username = request.user.username
        # pool_id = int(request.path_params['pool_id'])
        # vm_action = request.path_params['action']
        # in pool find machine which belongs to user
        vm_action = 'start'
        username = 'admin'
        pool_id = 28
        vms = yield Vm.get_vm_id(pool_id=pool_id, username=username)
        print('vms:')
        print(vms)

        if not vms:
            return self.finish({'error': 'Нет вм с указанным pool_id'})
        # if vms:
        #     [(vm_id,)] = vms

        # in body info about whether action is forced
        try:
            text_body = tornado.escape.json_decode(self.request.body)
        except ValueError:  # no response body
            text_body = ''
        print('do_action_on_vm: text_body', text_body)

        # determine vm controller ip by pool id
        controller_ip = yield Pool.get_controller(pool_id)
        print('controller_ip_', controller_ip)
        # do action
        yield VmHttpClient(controller_ip=controller_ip, vm_id=vms).send_action(action=vm_action, body=text_body)

        return self.finish({'error': 'null'})
