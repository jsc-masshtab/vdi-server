# -*- coding: utf-8 -*-
from abc import ABC
import asyncio

from tornado import websocket

from common.utils import cancel_async_task
from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import jwtauth
from pool.models import Pool, Vm, AutomatedPool
from vm.veil_client import VmHttpClient  # TODO: move to VM?

from pool.pool_task_manager import pool_task_manager


@jwtauth
class PoolHandler(BaseHandler, ABC):
    async def get(self):
        username = self.get_current_user()
        pools = await Pool.get_user_pools(username)
        response = {"data": pools}
        return self.finish(response)


@jwtauth
class PoolGetVm(BaseHandler, ABC):
    async def post(self, pool_id):
        # TODO: есть подозрение, что иногда несмотря на отправленный запрос на просыпание VM - отправляется
        #  недостаточное количество данных для подключения тонкого клиента
        username = self.get_current_user()

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
            [controller_ip, desktop_pool_type, vm_id] = free_vm
            await Vm.attach_vm_to_user(vm_id, username)
            # Логика древних:
            if desktop_pool_type == 'AUTOMATED':
                pool = await AutomatedPool.get(pool_id)
                #
                pool_lock = pool_task_manager.get_pool_lock(pool_id)
                template_lock = pool_task_manager.get_template_lock(pool_id)
                # Проверяем залочены ли локи. Если залочены, то ничего не делаем, так как любые другие действия с
                # пулом требующие блокировки - в приоретете.
                if not pool_lock.lock.locked() and not template_lock.lock.locked():
                    async with pool_lock.lock:
                        native_loop = asyncio.get_event_loop()
                        await cancel_async_task(pool_lock.expand_pool_task)
                        pool_lock.expand_pool_task = native_loop.create_task(pool.expand_pool_if_requred())

        vm_client = await VmHttpClient.create(controller_ip=controller_ip, vm_id=vm_id)
        info = await vm_client.info()
        # Проверяем включена ВМ и доступна ли для подключения.
        if Vm.ready_to_connect(**info):
            await vm_client.prepare()

        response = {'data': {'host': controller_ip,
                             'port': info['remote_access_port'],
                             'password': info['graphics_password']}
                    }

        return await self.finish(response)


@jwtauth
class ActionOnVm(BaseHandler, ABC):
    async def post(self, pool_id, action):
        vm_action = action
        username = self.get_current_user()

        vms = await Vm.get_vm_id(pool_id=pool_id, username=username)
        if not vms:
            return await self.finish({'error': 'Нет вм с указанным pool_id'})

        controller_ip = await Pool.get_controller_ip(pool_id)
        client = await VmHttpClient.create(controller_ip=controller_ip, vm_id=vms)
        await client.send_action(action=vm_action, body=self.args)
        return await self.finish({'error': 'null'})


class ThinClientWsHandler(websocket.WebSocketHandler):
    # def __init__(self, application: Application, request: httputil.HTTPServerRequest, **kwargs: Any):
    #     websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
    #     print('init')

    # todo: security problems. implement proper origin checking
    def check_origin(self, origin):
        return True
