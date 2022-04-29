# -*- coding: utf-8 -*-
from web_app.thin_client_api.handlers import (
    AddPoolToFavoriteHandler, AttachUsb, DetachUsb, GenerateUserQrCodeHandler, GetUserDataHandler,
    PoolGetVm, PoolHandler, RemovePoolFromFavoriteHandler,
    SendTextMsgHandler, ThinClientWsHandler, UpdateUserDataHandler, VmAction, VmDataHandler,
)


id_mask = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

thin_client_api_urls = [
    (r"/client/pools/?", PoolHandler),
    (
        rf"/client/pools/(?P<pool_id>{id_mask})/?",  # noqa: E501
        PoolGetVm,
    ),
    (
        rf"/client/pools/(?P<pool_id>{id_mask})/attach-usb/?",  # noqa: E501
        AttachUsb,
    ),
    (
        rf"/client/pools/(?P<pool_id>{id_mask})/detach-usb/?",  # noqa: E501
        DetachUsb,
    ),
    (
        rf"/client/pools/(?P<pool_id>{id_mask})/(?P<action>[a-z]+)/?",  # noqa: E501
        VmAction,
    ),
    (r"/ws/client/?", ThinClientWsHandler),
    (r"/client/send_text_message/?", SendTextMsgHandler),
    (r"/client/generate_user_qr_code/?", GenerateUserQrCodeHandler),
    (r"/client/get_user_data/?", GetUserDataHandler),
    (r"/client/update_user_data/?", UpdateUserDataHandler),
    (
        rf"/client/get_vm_data/(?P<vm_id>{id_mask})/?",
        VmDataHandler
    ),
    (
        rf"/client/pools/(?P<pool_id>{id_mask})/add-pool-to-favorite/?",  # noqa: E501
        AddPoolToFavoriteHandler,
    ),
    (
        rf"/client/pools/(?P<pool_id>{id_mask})/remove-pool-from-favorite/?",  # noqa: E501
        RemovePoolFromFavoriteHandler,
    ),
]
