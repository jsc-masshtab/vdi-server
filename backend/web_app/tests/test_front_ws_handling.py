# -*- coding: utf-8 -*-
import pytest
import json

import tornado
from tornado.testing import AsyncHTTPTestCase, gen_test

from web_app.front_ws_api.handlers import VdiFrontWsHandler


pytestmark = [pytest.mark.ws_requests]


class TestWebSockets(AsyncHTTPTestCase):
    """Check ws subscription mechanism"""
    def get_app(self):
        # dummy application
        app = tornado.web.Application([
            (r'/ws/subscriptions/?', VdiFrontWsHandler)
        ])
        return app

    @gen_test
    def test_websocket(self):
        # self.get_http_port() gives us the port of the running test server.
        ws_url = "ws://localhost:" + str(self.get_http_port()) + "/ws/subscriptions"

        ws_client = yield tornado.websocket.websocket_connect(ws_url)

        # valid subscribe
        ws_client.write_message('add /domains/')
        response = yield ws_client.read_message()
        data = json.loads(response)
        self.assertEqual(data['error'], False)

        # valid unsubscribe
        ws_client.write_message('delete /domains/')
        response = yield ws_client.read_message()
        data = json.loads(response)
        self.assertEqual(data['error'], False)

        # invalid subscribe
        # ws_client.write_message('add /wrong_resource/')
        # response = yield ws_client.read_message()
        # data = json.loads(response)
        # self.assertEqual(data['error'], True)
