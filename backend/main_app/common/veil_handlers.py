# -*- coding: utf-8 -*-
from abc import ABC
from tornado.web import RequestHandler
from tornado.escape import json_decode
from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler

from auth.utils.veil_jwt import extract_user, jwtauth, extract_user_object
from journal.journal import Log as log

# TODO: унифицировать обработку Exception, чтобы не плодить try:ex


class BaseHandler(RequestHandler, ABC):
    args = dict()

    def prepare(self):
        if self.request.headers.get('Content-Type') == 'application/json' and self.request.body:
            self.args = json_decode(self.request.body)

    def get_current_user(self):
        """Overridden tornado method"""
        return extract_user(self.request.headers)

    def log_finish(self, response):
        if 'data' in response:
            log.debug('BaseHandler data: {}'.format(response))
        else:
            log.debug('BaseHandler error: {}'.format(response))
        return self.finish(response)

    @property
    def remote_ip(self):
        remote_ip = self.request.headers.get("X-Real-IP") or self.request.headers.get(
            "X-Forwarded-For") or self.request.remote_ip
        return remote_ip

    @property
    def client_type(self):
        client_type = self.request.headers.get('Client-Type')
        return client_type if client_type else 'Unknown'

    @property
    def headers(self):
        return self.request.headers

    async def get_user_object(self):
        return await extract_user_object(self.headers)


@jwtauth
class VdiTornadoGraphQLHandler(TornadoGraphQLHandler, ABC):
    pass
