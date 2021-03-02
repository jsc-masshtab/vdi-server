# -*- coding: utf-8 -*-
import pytest
import json
import asyncio

import tornado
from tornado.testing import gen_test

from web_app.tests.utils import VdiHttpTestCase

from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from web_app.tests.utils import execute_scheme
from web_app.thin_client_api.schema import thin_client_schema
from common.settings import PAM_AUTH
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
    fixt_veil_client,  # noqa: F401
    get_auth_context,
)


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.ws_requests,
    pytest.mark.tk,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


class TestTk(VdiHttpTestCase):
    @pytest.mark.usefixtures("fixt_db", "fixt_user_admin")
    @gen_test
    async def test_ws_connect_update_disconnect_ok(self):
        """Check ws communication"""
        # login
        (user_name, access_token) = await self.do_login()

        # connect to ws
        ws_url = (
            "ws://localhost:" + str(self.get_http_port()) + "/ws/client?token={}"
            "&is_conn_init_by_user=0"
            "&veil_connect_version=1.4.1"
            "&tk_os=Linux".format(access_token)
        )
        ws_client = await tornado.websocket.websocket_connect(ws_url)
        assert ws_client

        try:
            # update
            vm_id = "201d318f-d57e-4f1b-9097-93d69f8782dd"
            update_data_dict = {
                "msg_type": "UPDATED",
                "vm_id": vm_id,
                "event": "vm_changed",
            }
            ws_client.write_message(json.dumps(update_data_dict))
            await asyncio.sleep(1)  # Подождем так как на update ответов не присылается

            user_id = await User.get_id(user_name)
            real_vm_id = (
                await ActiveTkConnection.select("vm_id")
                .where(ActiveTkConnection.user_id == user_id)
                .gino.scalar()
            )
            self.assertEqual(vm_id, str(real_vm_id))

            # test current connection data
            qu = """{
                    thin_clients_count
                }"""
            auth_context = await get_auth_context()
            executed = await execute_scheme(
                thin_client_schema, qu, context=auth_context
            )
            assert executed["thin_clients_count"] == 1
            # Получаем последнее подключение для юзера user_id
            qu = (
                """{
                        thin_clients(offset:0, limit: 1, ordering: "connected", user_id: "%s"){
                          conn_id
                          user_name
                          veil_connect_version
                          vm_name
                          tk_ip
                          tk_os
                          connected
                          data_received
                      }
                  }"""
                % user_id
            )
            auth_context = await get_auth_context()
            executed = await execute_scheme(
                thin_client_schema, qu, context=auth_context
            )
            assert len(executed["thin_clients"]) == 1
            assert executed["thin_clients"][0]["user_name"] == user_name

            conn_id = executed["thin_clients"][0]["conn_id"]

            # disconnect request
            qu = (
                """
                mutation{
                    disconnectThinClient(conn_id: "%s"){
                        ok
                    }
                }"""
                % conn_id
            )
            executed = await execute_scheme(
                thin_client_schema, qu, context=auth_context
            )
            assert executed["disconnectThinClient"]["ok"]

            # check tk statistics
            qu = (
                """{
                         thin_clients_statistics(limit:100, conn_id: "%s"){
                           id
                           conn_id
                           message
                           created
                         }
                    }"""
                % conn_id
            )
            executed = await execute_scheme(
                thin_client_schema, qu, context=auth_context
            )
            # Первое событие должно быть Login, второе - подключение к ВМ
            assert executed["thin_clients_statistics"][0][
                "message"
            ] == "{} connected.".format(user_name)
            assert executed["thin_clients_statistics"][1][
                "message"
            ] == "{} connected to VM .".format(user_name)

        except Exception:
            raise
        finally:
            # disconnect
            ws_client.close()
            await asyncio.sleep(0.1)

    @pytest.mark.usefixtures("fixt_db", "fixt_user_admin", "fixt_create_static_pool")
    @gen_test
    async def test_get_pool_info_ok(self):
        """Check tk rest api"""
        # login
        (user_name, access_token) = await self.do_login()

        # get pool data
        headers = {
            "Content-Type": "application/json",
            "Authorization": "jwt {}".format(access_token),
        }
        url = "/client/pools/"

        response_dict = await self.get_response(
            body=None, url=url, headers=headers, method="GET"
        )
        assert len(response_dict["data"]) == 1
