# -*- coding: utf-8 -*-
import pytest
import asyncio
import tornado
from tornado.testing import gen_test
from common.settings import PAM_AUTH

from web_app.tests.utils import VdiHttpTestCase, ws_wait_for_text_msg_with_timeout

from common.subscription_sources import WsMessageType, VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST

from web_app.tests.fixtures import (
    fixt_db,  # noqa: F401
    fixt_user_locked,  # noqa: F401
    fixt_user,  # noqa: F401
    fixt_user_admin,  # noqa: F401
    fixt_auth_dir,  # noqa: F401
    fixt_mapping,  # noqa: F401
    fixt_group,  # noqa: F401
    fixt_group_role,  # noqa: F401
    fixt_create_static_pool,  # noqa: F401
    fixt_controller,  # noqa: F401
    fixt_veil_client,  # noqa: F401
)  # noqa: F401


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.ws_requests,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


class TestWebSockets(VdiHttpTestCase):
    """Check ws subscription mechanism"""

    @pytest.mark.usefixtures("fixt_db", "fixt_user_admin")
    @gen_test
    async def test_subscribe_ok(self):
        # login
        (_, access_token) = await self.do_login()

        ws_client = None
        try:
            ws_client = await tornado.websocket.websocket_connect(self.get_ws_url(access_token))

            # valid subscribe
            for subscription in VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST:
                cmd = "add {}".format(subscription)
                # print("cmd: ", cmd, flush=True)
                ws_client.write_message(cmd)
                data = await ws_wait_for_text_msg_with_timeout(ws_client, WsMessageType.CONTROL.value)
                self.assertEqual(data["error"], False)

            # valid unsubscribe
            for subscription in VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST:
                cmd = "delete {}".format(subscription)
                # print("cmd: ", cmd, flush=True)
                ws_client.write_message(cmd)
                data = await ws_wait_for_text_msg_with_timeout(ws_client, WsMessageType.CONTROL.value)
                self.assertEqual(data["error"], False)

        finally:
            # disconnect
            if ws_client:
                ws_client.close()
                await asyncio.sleep(0.1)

    @pytest.mark.usefixtures("fixt_db", "fixt_user_admin")
    @gen_test
    async def test_subscribe_error(self):
        # login
        (_, access_token) = await self.do_login()

        ws_client = None
        try:
            ws_client = await tornado.websocket.websocket_connect(self.get_ws_url(access_token))

            ws_client.write_message("add /wrong_resource/")
            data = await ws_wait_for_text_msg_with_timeout(ws_client, WsMessageType.CONTROL.value)
            self.assertEqual(data["error"], True)
        finally:
            # disconnect
            if ws_client:
                ws_client.close()
                await asyncio.sleep(0.1)

    def get_ws_url(self, access_token):
        return (
                "ws://localhost:"
                + str(self.get_http_port())  # noqa: W503
                + "/ws/subscriptions?token={}".format(access_token)  # noqa: W503
        )
