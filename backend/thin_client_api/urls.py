# -*- coding: utf-8 -*-
from thin_client_api.handlers import PoolHandler, PoolGetVm, ActionOnVm, ThinClientWsHandler


thin_client_api_urls = [
    (r'/client/pools/?', PoolHandler),
    (r'/client/pools/(?P<pool_id>[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12})/?',
     PoolGetVm),
    (r'/client/pools/(?P<pool_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/(?P<action>[a-z]+)/?',
     ActionOnVm),
    (r'/ws/client/vdi_server_check/?', ThinClientWsHandler)
]
