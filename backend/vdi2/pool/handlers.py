# -*- coding: utf-8 -*-
from abc import ABC
from tornado import gen
from tornado import websocket

import json  # TODO: remove me

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import jwtauth
from pool.models import Pool
# from pool.schema import DesktopPoolType


@jwtauth
class PoolHandler(BaseHandler, ABC):
    # TODO: move old code
    @gen.coroutine
    def get(self):
        # TODO: add user
        pools = yield Pool.get_pools()
        self.finish(json.dumps(pools))  # TODO: because Tornado don't recomends to send list. Think about it.


# class PoolGetVm(BaseHandler, ABC):
#     # TODO: from where user?
#
#     @gen.coroutine
#     def post(self):
#         print('i am here')
#         # Сочитание pool id и имя пользователя должно быть обязательо уникальным
#         # так как пользователь не может иметь больше одной машины в пуле
#         data = yield Pool.get_user_pools()
#
#     # user = request.user.username  # TODO: from where?
#     # pool_id = int(request.path_params['pool_id'])
#
#         if not data:
#             self.write({'host': '', 'port': 0, 'password': '',
#                         'message': 'Пул не найден'})
#
#         [[controller_ip, desktop_pool_type, vm_id]] = data  # TODO: smells like teen spirit
#         print('data', data)
#         if vm_id:
#             from tasks.vm import GetDomainInfo
#             from tasks import thin_client
#             print('1')
#             info = yield GetDomainInfo(controller_ip=controller_ip, domain_id=vm_id)
#             print('2')
#             yield thin_client.PrepareVm(controller_ip=controller_ip, domain_id=vm_id)
#             print('remote_access_port', info['remote_access_port'])
#             self.write({
#                     'host': controller_ip,
#                     'port': info['remote_access_port'],
#                     'password': info['graphics_password'],
#                     })
#     # # If the user does not have a vm in the pool then try to assign a free vm to him
#     # # find a free vm in pool
#     # async with db.connect() as conn:
#     #     qu = "select id from vm where pool_id = $1 and username is NULL limit 1", pool_id
#     #     free_vm = await
#     #     conn.fetch(*qu)
#     #     print('get_vm: free_vm', free_vm)
#     #     # if there is no free vm then send empty fields??? Handle on thin client side
#     #     if not free_vm:
#     #         return JSONResponse({'host': '', 'port': 0, 'password': '',
#     #                              'message': 'В пуле нет свободных машин'})
#     #     # assign vm to the user
#     #     [(domain_id,)] = free_vm
#     #
#     #     qu = "update vm set username = $1 where id = $2", user, domain_id
#     #     await
#     #     conn.fetch(*qu)
#     #
#     # # post actions for AUTOMATED pool (todo: run in another courutine)
#     # if desktop_pool_type == DesktopPoolType.AUTOMATED.name:
#     #     # try to wake pool if it's empty
#     #     if pool_id not in Pool.instances:
#     #         await
#     #         Pool.wake_pool(pool_id)
#     #     pool = Pool.instances[pool_id]
#     #     await
#     #     pool.on_vm_taken()
#     #
#     # # send data to thin client
#     # info = await
#     # thin_client.PrepareVm(controller_ip=controller_ip, domain_id=domain_id)
#     # return JSONResponse({
#     #     'host': controller_ip,
#     #     'port': info['remote_access_port'],
#     #     'password': info['graphics_password'],
#     # })
# async def vdi_online_ws_endpoint(websocket):
#
#     await websocket.accept()
#     try:
#         while True:
#             await websocket.send_bytes(b"1")
#             await asyncio.sleep(WS_TIMEOUT)
#     except WsConnectionClosed:
#         pass


class EchoWebSocket(websocket.WebSocketHandler, ABC):
    pass
