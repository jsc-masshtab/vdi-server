# -*- coding: utf-8 -*-
from tornado.websocket import WebSocketHandler
from thin_client_api.handlers import PoolHandler, PoolGetVm, ActionOnVm, AuthHandler

# TODO: сейчас айдишники пулов это ИНТ, есть сомнения, что это хорошая идея.
#  Возможно надо заменить на UUID, тогда потребуется обновить регулярку

thin_client_api_urls = [
    (r'/auth/?', AuthHandler),  # client url
    (r'/client/pools/?', PoolHandler),
    (r'/client/pools/(?P<pool_id>[0-9]+)/?', PoolGetVm),
    (r'/client/pools/(?P<pool_id>[0-9]+)/(?P<action>[a-z]+)/?', ActionOnVm),  # action must be in lower case
    (r'/ws/client/vdi_server_check/?', WebSocketHandler)
]
