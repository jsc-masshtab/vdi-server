# -*- coding: utf-8 -*-
from web_app.thin_client_api.handlers import (PoolHandler, PoolGetVm, VmAction,
                                              ThinClientWsHandler, RedisInfoHandler,
                                              AttachUsb, DetachUsb)


thin_client_api_urls = [
    (r'/client/pools/?', PoolHandler),
    (r'/client/pools/(?P<pool_id>[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12})/?',
     PoolGetVm),
    (r'/client/pools/(?P<pool_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/attach-usb/?',  # noqa: E501
     AttachUsb),
    (r'/client/pools/(?P<pool_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/detach-usb/?',  # noqa: E501
     DetachUsb),
    (r'/client/pools/(?P<pool_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/(?P<action>[a-z]+)/?',  # noqa: E501
     VmAction),
    (r'/ws/client/?', ThinClientWsHandler),
    (r'/client/message_broker/?', RedisInfoHandler)
]
