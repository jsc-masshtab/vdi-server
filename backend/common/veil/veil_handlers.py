# -*- coding: utf-8 -*-
from abc import ABC
from tornado.web import RequestHandler
from tornado.escape import json_decode
from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler

from common.veil.auth.veil_jwt import extract_user, jwtauth, extract_user_object
from common.models.auth import User
from common.log.journal import system_logger

# TODO: унифицировать обработку Exception, чтобы не плодить try:ex


class BaseHandler(RequestHandler, ABC):
    args = dict()

    def prepare(self):
        if self.request.headers.get('Content-Type') == 'application/json' and self.request.body:
            self.args = json_decode(self.request.body)

    def get_current_user(self):
        """Overridden tornado method."""
        return extract_user(self.request.headers)

    async def get_user_model_instance(self):
        """Возвращает объект модели User."""
        # Извлекаем username из токена
        username = extract_user(self.request.headers)
        # Формируем запрос
        query = User.query.where(User.username == username).where(User.is_active)
        return await query.gino.first()

    async def log_finish(self, response):
        if 'data' in response:
            await system_logger.debug('BaseHandler data: {}'.format(response))
        else:
            await system_logger.debug('BaseHandler error: {}'.format(response))
        return self.finish(response)

    @property
    def remote_ip(self):
        remote_ip = self.request.headers.get("X-Real-IP") or self.request.headers.get(
            "X-Forwarded-For") or self.request.remote_ip
        return remote_ip

    @property
    def client_type(self):
        client_type = self.request.headers.get('User-Agent')
        return client_type if client_type else 'Unknown'

    @property
    def headers(self):
        return self.request.headers

    async def get_user_object(self):
        return await extract_user_object(self.headers)


@jwtauth
class VdiTornadoGraphQLHandler(TornadoGraphQLHandler, ABC):
    pass
