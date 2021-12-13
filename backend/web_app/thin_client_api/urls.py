# -*- coding: utf-8 -*-
from web_app.thin_client_api.handlers import (
    AttachUsb, DetachUsb, GenerateUserQrCodeHandler, GetUserDataHandler, PoolGetVm, PoolHandler,
    SendTextMsgHandler, ThinClientWsHandler, UpdateUserDataHandler, VmAction, VmDataHandler
)


thin_client_api_urls = [
    (r"/client/pools/?", PoolHandler),
    (
        r"/client/pools/(?P<pool_id>[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12})/?",  # noqa: E501
        PoolGetVm,
    ),
    (
        r"/client/pools/(?P<pool_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/attach-usb/?",  # noqa: E501
        AttachUsb,
    ),
    (
        r"/client/pools/(?P<pool_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/detach-usb/?",  # noqa: E501
        DetachUsb,
    ),
    (
        r"/client/pools/(?P<pool_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/(?P<action>[a-z]+)/?",  # noqa: E501
        VmAction,
    ),
    (r"/ws/client/?", ThinClientWsHandler),
    (r"/client/send_text_message/?", SendTextMsgHandler),
    (r"/client/generate_user_qr_code/?", GenerateUserQrCodeHandler),
    (r"/client/get_user_data/?", GetUserDataHandler),
    (r"/client/update_user_data/?", UpdateUserDataHandler),
    (
        r"/client/get_vm_data/(?P<vm_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/?",
        VmDataHandler
    ),
]
