# -*- coding: utf-8 -*-
from pool.handlers import PoolHandler, EchoWebSocket
    # PoolGetVm, \

# TODO: add routing
pool_urls = [
    (r'/client/pools/?', PoolHandler),  # client url
    # TODO: fix handlers
    # (r'/client/pools/28/?', PoolGetVm),  # client url
    # (r'/client/pools/{pool_id}/?', PoolGetVm),  # client url
    # (r'/client/pools/{pool_id}/{action}/?', PoolHandler),  # client url
    (r'/ws/client/vdi_server_check/?', EchoWebSocket),  # client url
    # TODO: websocket url
]
