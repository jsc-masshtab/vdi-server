# -*- coding: utf-8 -*-
from abc import ABC
from tornado.web import RequestHandler
from tornado.escape import json_decode

from auth.utils.veil_jwt import extract_user

# TODO: унифицировать обработку Exception, чтобы не плодить try:ex


class BaseHandler(RequestHandler, ABC):
    args = dict()

    def prepare(self):
        if self.request.headers.get('Content-Type') == 'application/json' and self.request.body:
            self.args = json_decode(self.request.body)

    def get_current_user(self):
        """Overridden tornado method"""
        return extract_user(self.request.headers)
