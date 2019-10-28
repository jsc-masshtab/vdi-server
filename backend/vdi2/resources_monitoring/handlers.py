# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from tornado import websocket
from tornado import gen


class VdiFrontWebSocket(websocket.WebSocketHandler):

    # todo: security problems. implement proper origin checking
    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        print('message', message)
        #self.write_message(message)

    def on_close(self):
        print("WebSocket closed")
