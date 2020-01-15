# -*- coding: utf-8 -*-
from abc import ABC
import asyncio

from tornado import websocket

from common.utils import cancel_async_task
from common.veil_handlers import BaseHandler
from common.veil_errors import HttpError

from auth.utils.veil_jwt import jwtauth
from pool.models import Pool, Vm, AutomatedPool
from vm.veil_client import VmHttpClient  # TODO: move to VM?

from pool.pool_task_manager import pool_task_manager

from  controller.models import Controller

from database import db


@jwtauth
class PoolHandler(BaseHandler, ABC):
    async def get(self):
        username = self.get_current_user()
        pools = await Pool.get_user_pools(username)
        response = {"data": pools}
        return self.finish(response)


@jwtauth
class PoolGetVm(BaseHandler, ABC):

    async def post(self, pool_id):  # remote_protocol: rdp/spice
        # TODO: есть подозрение, что иногда несмотря на отправленный запрос на просыпание VM - отправляется
        #  недостаточное количество данных для подключения тонкого клиента
        username = self.get_current_user()

        # Древние говорили, что сочитание pool id и имя пользователя должно быть обязательно уникальным
        # так как пользователь не может иметь больше одной машины в пуле
        # get pool data
        pool_data = await Pool.get_pool(pool_id)
        if not pool_data:
            response_dict = {'data': dict(host='', port=0, password='', message='Пул не найден')}
            return await self.finish(response_dict)

        controller_ip = await Controller.select('address').where(Controller.id == pool_data.controller).gino.scalar()

        # get vm from pool
        vm_data = await Vm.select('id').where((Vm.pool_id == pool_id) & (Vm.username == username)).gino.first()
        if not vm_data:
            # Древние говорили, что если у пользователя нет VM в пуле, то нужно попытаться назначить ему свободную VM.
            vm_id = await Vm.get_free_vm_id_from_pool(pool_id)
            # Если свободная VM найдена, нужно закрепить ее за пользователем.
            if vm_id:
                await Vm.attach_vm_to_user(vm_id, username)
        else:
            vm_id = vm_data.id

        # В отдельной корутине запускаем расширение пула
        if pool_data.pool_type == 'AUTOMATED':
            pool = await AutomatedPool.get(pool_id)
            #
            pool_lock = pool_task_manager.get_pool_lock(pool_id)
            template_lock = pool_task_manager.get_template_lock(str(pool.template_id))
            # Проверяем залочены ли локи. Если залочены, то ничего не делаем, так как любые другие действия с
            # пулом требующие блокировки - в приоретете.
            if not pool_lock.lock.locked() and not template_lock.lock.locked():
                async with pool_lock.lock:
                    native_loop = asyncio.get_event_loop()
                    await cancel_async_task(pool_lock.expand_pool_task)
                    pool_lock.expand_pool_task = native_loop.create_task(pool.expand_pool_if_requred())

        if not vm_id:
            response_dict = {'data': dict(host='', port=0, password='', message='В пуле нет свободных машин')}
            return await self.finish(response_dict)
        else:
            #  Опытным путем было выяснено, что vm info содержит remote_access_port None, пока не врубишь
            # удаленный доступ. Поэтому врубаем его без проверки, чтоб не запрашивать инфу 2 раза
            vm_client = await VmHttpClient.create(controller_ip=str(controller_ip), vm_id=str(vm_id))

            # Опытным путем установлено: если машина уже включена, то запрос может вернуться с 400.  Поэтому try
            try:
                await vm_client.prepare()
            except HttpError:
                pass

            info = await vm_client.info()

            remote_protocol = self.args['remote_protocol']
            if remote_protocol == 'rdp':
                try:
                    vm_address = info['guest_utils']['ipv4'][0]
                except (IndexError, KeyError):
                    response_dict = {'data': dict(host='', port=0, password='',
                                                  message='Не удалось получить адресс ВМ для подключения по RDP')}
                    return await self.finish(response_dict)

            else:  # spice by default
                vm_address = str(controller_ip)

            response = {'data': dict(host=vm_address,
                                     port=info['remote_access_port'],
                                     password=info['graphics_password'],
                                     vm_verbose_name=info['verbose_name'])
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
