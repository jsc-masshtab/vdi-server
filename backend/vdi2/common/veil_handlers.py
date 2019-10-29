# -*- coding: utf-8 -*-
from abc import ABC
from tornado.web import RequestHandler
from tornado.escape import json_decode

from auth.utils.veil_jwt import extract_user


class BaseHandler(RequestHandler, ABC):
    args = dict()

    def prepare(self):
        # TODO: нужно добавить заголовок на тонком клиенте, чтобы явно обрабатывать запросы.
        # if self.request.headers.get('Content-Type') == 'application/json' and self.request.body:
        if self.request.body:
            self.args = json_decode(self.request.body)

    def get_current_user(self):
        """Overridden tornado method"""
        return extract_user(self.request.headers)
