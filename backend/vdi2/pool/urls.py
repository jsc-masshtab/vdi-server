# -*- coding: utf-8 -*-
from pool.handlers import PoolHandler, EchoWebSocket, PoolGetVm, ActionOnVm

# TODO: add routing
pool_urls = [
    (r'/client/pools/?', PoolHandler),  # client url
    # TODO: fix handlers
    (r'/client/pools/59/?', PoolGetVm),  # client url
    # (r'/client/pools/{pool_id}/?', PoolGetVm),  # client url
    (r'/client/pools/59/start/?', ActionOnVm),  # client url
    (r'/ws/client/vdi_server_check/?', EchoWebSocket),  # client url
    # TODO: websocket url
]
