# -*- coding: utf-8 -*-
import pytest
import json
import asyncio

import tornado
from tornado.testing import gen_test
from web_app.auth.handlers import AuthHandler

from web_app.tests.utils import VdiHttpTestCase
from web_app.thin_client_api.handlers import ThinClientWsHandler

from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User

from web_app.tests.fixtures import (fixt_db, fixt_user_locked, fixt_user, fixt_user_admin, fixt_auth_dir,  # noqa
                            fixt_mapping, fixt_group, fixt_group_role)  # noqa


pytestmark = [pytest.mark.asyncio, pytest.mark.auth, pytest.mark.ws_requests]


class TestTkWebSockets(VdiHttpTestCase):
    """Check ws subscription mechanism"""
    def get_app(self):
        # dummy application
        app = tornado.web.Application([
            (r'/ws/client/vdi_server_check/?', ThinClientWsHandler),
            (r'/auth/?', AuthHandler)
        ])
        return app

    @pytest.mark.usefixtures('fixt_db', 'fixt_user_admin')
    @gen_test
    def test_websocket(self):
        # login
        user_name = "test_user_admin"
        body = {"username": user_name, "password": "veil"}
        response_dict = yield self.get_response(body=json.dumps(body))
        access_token = response_dict['data']['access_token']
        self.assertTrue(access_token)
        # print('!!!access_token ', access_token, flush=True)

        # connect to ws
        ws_url = "ws://localhost:" + str(self.get_http_port()) + "/ws/client/vdi_server_check"
        ws_client = yield tornado.websocket.websocket_connect(ws_url)

        # auth
        auth_data_dict = {"msg_type": "AUTH", "token": access_token, "veil_connect_version": "1.3.4",
                          "vm_name": None, "tk_os": 'Linux', 'vm_id': None}
        ws_client.write_message(json.dumps(auth_data_dict))

        # check success
        response = yield ws_client.read_message()
        self.assertEqual(response, 'Auth success')

        # update
        vm_id = "201d318f-d57e-4f1b-9097-93d69f8782dd"
        update_data_dict = {"msg_type": "UPDATED", "vm_id": vm_id}
        ws_client.write_message(json.dumps(update_data_dict))
        yield asyncio.sleep(0.2)  # Подождем так как на update ответов не присылается

        user_id = yield User.get_id(user_name)
        real_vm_id = yield ActiveTkConnection.select('vm_id').where(ActiveTkConnection.user_id == user_id).\
            gino.scalar()
        self.assertEqual(vm_id, str(real_vm_id))

        ws_client.close()
        yield asyncio.sleep(0.1)
