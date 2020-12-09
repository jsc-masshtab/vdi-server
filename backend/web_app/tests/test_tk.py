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

from web_app.tests.fixtures import (fixt_db, fixt_user_locked, fixt_user, fixt_user_admin, fixt_auth_dir,  # noqa
                            fixt_mapping, fixt_group, fixt_group_role, fixt_create_static_pool, # noqa
                                    fixt_controller, fixt_veil_client, get_auth_context)  # noqa


pytestmark = [pytest.mark.asyncio, pytest.mark.ws_requests, pytest.mark.tk]


class TestTk(VdiHttpTestCase):

    async def do_login(self):
        user_name = "test_user_admin"
        body = {"username": user_name, "password": "veil"}
        response_dict = await self.get_response(body=json.dumps(body))
        access_token = response_dict['data']['access_token']
        self.assertTrue(access_token)

        return user_name, access_token

    @pytest.mark.usefixtures('fixt_db', 'fixt_user_admin')
    @gen_test
    async def test_ws_connect_update_disconnect_ok(self):
        """Check ws communication"""
        # login
        (user_name, access_token) = await self.do_login()

        # connect to ws
        ws_url = "ws://localhost:" + str(self.get_http_port()) + "/ws/client/vdi_server_check"
        ws_client = await tornado.websocket.websocket_connect(ws_url)

        try:
            # auth
            auth_data_dict = {"msg_type": "AUTH", "token": access_token, "veil_connect_version": "1.3.4",
                              "vm_name": None, "tk_os": 'Linux', 'vm_id': None}
            ws_client.write_message(json.dumps(auth_data_dict))

            # check success
            response = await ws_client.read_message()
            res_data_dict = json.loads(response)
            self.assertEqual(res_data_dict['msg'], 'Auth success')

            # update
            vm_id = "201d318f-d57e-4f1b-9097-93d69f8782dd"
            update_data_dict = {"msg_type": "UPDATED", "vm_id": vm_id, "event": "vm_changed"}
            ws_client.write_message(json.dumps(update_data_dict))
            await asyncio.sleep(1)  # Подождем так как на update ответов не присылается

            user_id = await User.get_id(user_name)
            real_vm_id = await ActiveTkConnection.select('vm_id').where(ActiveTkConnection.user_id == user_id).\
                gino.scalar()
            self.assertEqual(vm_id, str(real_vm_id))

            # test current data
            qu = """{
                    thin_clients_count
                }"""
            auth_context = await get_auth_context()
            executed = await execute_scheme(thin_client_schema, qu, context=auth_context)
            assert executed['thin_clients_count'] == 1
            #
            qu = """{
                        thin_clients(offset:0, limit: 100, ordering: "user_name"){
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
            auth_context = await get_auth_context()
            executed = await execute_scheme(thin_client_schema, qu, context=auth_context)
            assert len(executed['thin_clients']) == 1
            assert executed['thin_clients'][0]['user_name'] == user_name

            # disconnect request
            conn_id = executed['thin_clients'][0]['conn_id']
            qu = """
                mutation{
                    disconnectThinClient(conn_id: "%s"){
                        ok
                    }
                }""" % conn_id
            executed = await execute_scheme(thin_client_schema, qu, context=auth_context)
            assert executed['disconnectThinClient']['ok']

        except Exception:
            raise
        finally:
            # disconnect
            ws_client.close()
            await asyncio.sleep(0.1)

    @pytest.mark.usefixtures('fixt_db', 'fixt_user_admin', 'fixt_create_static_pool')
    @gen_test
    async def test_get_pool_info_ok(self):
        """Check tk rest api"""
        # login
        (user_name, access_token) = await self.do_login()

        # get pool data
        headers = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}
        url = '/client/pools/'

        response_dict = await self.get_response(body=None, url=url, headers=headers, method='GET')
        assert len(response_dict['data']) == 1
