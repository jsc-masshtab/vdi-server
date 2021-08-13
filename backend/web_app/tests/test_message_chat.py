# -*- coding: utf-8 -*-
"""Тестировавние передачи сообщений между админом и пользователем
"""

import pytest
import json
import asyncio

import tornado
from tornado.testing import gen_test

from common.models.auth import User

from web_app.thin_client_api.schema import thin_client_schema

from web_app.tests.utils import VdiHttpTestCase
from web_app.tests.utils import execute_scheme, ws_wait_for_text_msg_with_timeout

from common.subscription_sources import (
    USERS_SUBSCRIPTION,
    WsMessageType,
    WsMessageDirection,
)

from common.settings import AUTH_ENABLED, PAM_AUTH

from web_app.tests.fixtures import (
    fixt_db,  # noqa: F401
    fixt_redis_client,
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
    get_auth_context,
)  # noqa: F401

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.ws_requests,
    pytest.mark.tk,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


class TestMessageChat(VdiHttpTestCase):
    @pytest.mark.usefixtures("fixt_db", "fixt_user", "fixt_user_admin")
    @gen_test
    async def test_chat_ok(self):
        """Тестируется сценарий общения пользователя с админом"""
        tk_ws_client = None
        admin_ws_client = None
        try:
            # Thin client login
            tk_user_name = "test_user"
            (tk_user_name, tk_access_token) = await self.do_login(
                user_name=tk_user_name, password="veil"
            )

            # Thin client connection to ws
            ws_url = (
                "ws://localhost:" + str(self.get_http_port()) + "/ws/client?token={}"
                "&is_conn_init_by_user=0"
                "&veil_connect_version=1.4.1"
                "&tk_os=Linux".format(tk_access_token)
            )
            tk_ws_client = await tornado.websocket.websocket_connect(ws_url)
            assert tk_ws_client

            # Admin login
            admin_name = "vdiadmin"
            (admin_name, admin_access_token) = await self.do_login(
                user_name=admin_name, password="Bazalt1!"
            )

            #  Admin connection to ws
            ws_url = (
                "ws://localhost:"
                + str(self.get_http_port())  # noqa: W504
                + "/ws/subscriptions?token={}".format(admin_access_token)  # noqa: W504
            )

            admin_ws_client = await tornado.websocket.websocket_connect(ws_url)
            assert admin_ws_client

            #  ADMIN -> USER
            #
            # Admin sends message to thin client
            tk_user_id = await User.get_id(tk_user_name)
            test_text_message_to_tk = "test message to thin client"
            qu = """mutation{
                    sendMessageToThinClient(recipient_id: "%s", message: "%s"){
                        ok
                    }
                 }""" % (
                tk_user_id,
                test_text_message_to_tk,
            )
            auth_context = await get_auth_context()
            executed = await execute_scheme(
                thin_client_schema, qu, context=auth_context
            )
            assert executed["sendMessageToThinClient"]["ok"]

            # Thin client waits for test text message
            # Должно прийти очень быстро
            tk_received_msg_dict = await ws_wait_for_text_msg_with_timeout(tk_ws_client)

            # print('tk_received_msg_dict: ', tk_received_msg_dict, flush=True)
            assert tk_received_msg_dict["msg_type"] == WsMessageType.TEXT_MSG.value
            assert tk_received_msg_dict["message"] == test_text_message_to_tk
            if AUTH_ENABLED:
                assert tk_received_msg_dict["sender_name"] == admin_name
            assert (
                tk_received_msg_dict["direction"]
                == WsMessageDirection.ADMIN_TO_USER.value
            )
            assert tk_received_msg_dict["recipient_id"] == str(tk_user_id)

            # USER -> ADMIN
            #
            # Админ подписывается на получение сообщений от пользователей
            admin_ws_client.write_message("add {}".format(USERS_SUBSCRIPTION))
            admin_received_msg_dict = await ws_wait_for_text_msg_with_timeout(
                ws_conn=admin_ws_client, msg_type=WsMessageType.CONTROL.value)

            self.assertEqual(
                admin_received_msg_dict["error"], False
            )  # Проверка успешности подписки

            # Thin client send message to admins
            # Тонкий клиент шлет сообщение всем админам, так как у нет и не может быть информации о списках админов
            tk_msg_headers = {
                "Content-Type": "application/json",
                "Authorization": "jwt {}".format(tk_access_token),
            }

            test_text_message_to_admin = "test message to admins"
            tk_msg_data_dict = dict(message=test_text_message_to_admin)

            response = await self.fetch_request(
                url="/client/send_text_message",
                headers=tk_msg_headers,
                body=json.dumps(tk_msg_data_dict),
            )
            self.assertEqual(response.code, 200)

            # Получение сообщение админом от тк
            admin_received_msg_dict = await ws_wait_for_text_msg_with_timeout(admin_ws_client)

            assert admin_received_msg_dict["msg_type"] == WsMessageType.TEXT_MSG.value
            assert admin_received_msg_dict["message"] == test_text_message_to_admin
            assert admin_received_msg_dict["resource"] == USERS_SUBSCRIPTION
            assert (
                admin_received_msg_dict["direction"]
                == WsMessageDirection.USER_TO_ADMIN.value
            )
            assert admin_received_msg_dict["sender_id"] == str(tk_user_id)

        finally:
            # disconnect
            if tk_ws_client:
                tk_ws_client.close()
            if admin_ws_client:
                admin_ws_client.close()
            await asyncio.sleep(0.1)

    @staticmethod
    async def wait_for_text_msg(ws_conn, msg_type=WsMessageType.TEXT_MSG.value):
        while True:
            msg = await ws_conn.read_message()
            msg_dict = json.loads(msg)
            if msg_dict["msg_type"] == msg_type:
                return msg_dict
