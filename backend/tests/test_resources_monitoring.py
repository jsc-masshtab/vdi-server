# TODO: старая и не рабочая версия. Нужно переписать.
import pytest
import json

import tornado
from tornado.testing import AsyncHTTPTestCase, gen_test

from resources_monitoring.handlers import VdiFrontWsHandler


@pytest.mark.websokets
class TestWebSockets(AsyncHTTPTestCase):
    def get_app(self):
        # dummy application
        app = tornado.web.Application([
            (r'/subscriptions/?', VdiFrontWsHandler)
        ])
        return app

    @gen_test
    def test_websocket(self):
        # self.get_http_port() gives us the port of the running test server.
        ws_url = "ws://localhost:" + str(self.get_http_port()) + "/subscriptions"

        ws_client = yield tornado.websocket.websocket_connect(ws_url)

        # subscribe
        ws_client.write_message('add /domains/')
        response = yield ws_client.read_message()
        data = json.loads(response)
        self.assertEqual(data['error'], False)

        # unsubscribe
        ws_client.write_message('delete /domains/')
        response = yield ws_client.read_message()
        data = json.loads(response)
        self.assertEqual(data['error'], False)

