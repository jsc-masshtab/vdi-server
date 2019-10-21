# -*- coding: utf-8 -*-
from abc import ABC
import tornado.web


class BaseHandler(tornado.web.RequestHandler, ABC):
    args = dict()

    def prepare(self):
        # if self.request.headers.get('Content-Type') == 'application/x-json' and self.request.body:
        if self.request.body:
            self.args = tornado.escape.json_decode(self.request.body)
