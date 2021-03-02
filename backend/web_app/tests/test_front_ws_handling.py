# -*- coding: utf-8 -*-
import pytest
import json
import tornado
from tornado.testing import gen_test
from common.settings import PAM_AUTH

from web_app.tests.utils import VdiHttpTestCase
from web_app.tests.fixtures import (
    fixt_db,
    fixt_user_locked,
    fixt_user,
    fixt_user_admin,  # noqa: F401
    fixt_auth_dir,
    fixt_mapping,
    fixt_group,
    fixt_group_role,  # noqa: F401
    fixt_create_static_pool,
    fixt_controller,
    fixt_veil_client,
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
    async def test_websocket(self):
        # login
        (user_name, access_token) = await self.do_login()

        # self.get_http_port() gives us the port of the running test server.
        ws_url = (
            "ws://localhost:"
            + str(self.get_http_port())
            + "/ws/subscriptions?token={}".format(access_token)
        )

        ws_client = await tornado.websocket.websocket_connect(ws_url)

        # valid subscribe
        ws_client.write_message("add /domains/")
        response = await ws_client.read_message()
        data = json.loads(response)
        self.assertEqual(data["error"], False)

        # valid unsubscribe
        ws_client.write_message("delete /domains/")
        response = await ws_client.read_message()
        data = json.loads(response)
        self.assertEqual(data["error"], False)

        # invalid subscribe
        ws_client.write_message("add /wrong_resource/")
        response = await ws_client.read_message()
        data = json.loads(response)
        self.assertEqual(data["error"], True)
