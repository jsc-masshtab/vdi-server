# -*- coding: utf-8 -*-
from tornado.websocket import WebSocketHandler
from thin_client_api.handlers import PoolHandler, PoolGetVm, ActionOnVm, AuthHandler, RefreshAuthHandler

# TODO: сейчас айдишники пулов это ИНТ, есть сомнения, что это хорошая идея.
#  Возможно надо заменить на UUID, тогда потребуется обновить регулярку

thin_client_api_urls = [
    (r'/auth/?', AuthHandler),
    (r'/auth/refresh-token/?', RefreshAuthHandler),
    (r'/client/pools/?', PoolHandler),
    (r'/client/pools/(?P<pool_uid>[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12})/?',
     PoolGetVm),
    (r'/client/pools/(?P<pool_uid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/(?P<action>[a-z]+)/?',
     ActionOnVm),
    (r'/ws/client/vdi_server_check/?', WebSocketHandler)
]
