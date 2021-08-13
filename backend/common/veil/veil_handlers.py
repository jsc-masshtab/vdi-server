# -*- coding: utf-8 -*-
import textwrap
from abc import ABC
from typing import Any, Awaitable, Optional

from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler

from tornado import httputil, websocket
from tornado.escape import json_decode
from tornado.web import Application, RequestHandler

from common.languages import _local_
from common.log.journal import system_logger
from common.models.auth import User
from common.models.pool import Pool
from common.veil.auth.veil_jwt import (
    extract_user,
    extract_user_object,
    jwtauth,
)
from common.veil.veil_errors import InvalidUserError, ValidationError


class BaseHandler(RequestHandler, ABC):
    @property
    def remote_ip(self):
        remote_ip = (
            self.request.headers.get("X-Real-IP")
            or self.request.headers.get("X-Forwarded-For")  # noqa: W503
            or self.request.remote_ip  # noqa: W503
        )
        return remote_ip


class BaseHttpHandler(BaseHandler):
    args = dict()

    def prepare(self):
        if (
            self.request.headers.get("Content-Type") == "application/json"
            and self.request.body  # noqa: W503
        ):
            self.args = json_decode(self.request.body)

    def get_current_user(self):
        """Overridden tornado method."""
        return extract_user(self.request.headers)

    async def get_user_model_instance(self):
        """Возвращает объект модели User."""
        # Извлекаем username из токена
        username = extract_user(self.request.headers)
        # Формируем запрос
        user = (
            await User.query.where(User.username == username)
            .where(User.is_active)
            .gino.first()
        )

        if not user:
            raise InvalidUserError(_local_("User {} not found.").format(username))

        return user

    async def log_finish(self, response):
        if "data" in response:
            await system_logger.debug("BaseHttpHandler data: {}".format(response))
        else:
            await system_logger.debug("BaseHttpHandler error: {}".format(response))
        return self.finish(response)

    @property
    def client_type(self):
        client_type = self.request.headers.get("User-Agent")
        return client_type if client_type else "Unknown"

    @property
    def headers(self):
        return self.request.headers

    async def get_user_object(self):
        return await extract_user_object(self.headers)

    def validate_and_get_parameter(self, parameter_name: str, default_value=None):

        parameter_value = self.args.get(parameter_name, default_value)
        if parameter_value is None:
            raise ValidationError("Parameter {} required.".format(parameter_name))

        return parameter_value

    @staticmethod
    async def validate_and_get_vm(user, pool_id):
        if not user:
            raise InvalidUserError(_local_("User {} not found."))

        pool = await Pool.get(pool_id)
        if not pool:
            raise ValidationError(
                _local_("There is no pool with id: {}.").format(pool_id))
        vm = await pool.get_vm(user_id=user.id)
        if not vm:
            raise ValidationError(
                _local_("User {} has no VM on pool {}.").format(user.username, pool.id)
            )

        return vm

    def write_error(self, status_code, **kwargs):
        """Согласно доке вызывается если возникло неотработанное исключение при обработка запроса."""
        message = "Uncaught exception"
        try:
            exc_info = kwargs["exc_info"]
            (_, exc, _) = exc_info
            message = "Server error: " + str(exc)
        finally:
            shorten_msg = textwrap.shorten(message, width=100)
            response = {"errors": [{"message": shorten_msg}]}
            self.write(response)


@jwtauth
class VdiTornadoGraphQLHandler(TornadoGraphQLHandler, ABC):
    pass


class BaseWsHandler(BaseHandler, websocket.WebSocketHandler):
    def __init__(
        self,
        application: Application,
        request: httputil.HTTPServerRequest,
        **kwargs: Any
    ):
        super().__init__(application, request, **kwargs)

        self.user_id = None

    def check_origin(self, origin):
        return True

    async def write_msg(self, msg):
        try:
            await self.write_message(msg)
        except (websocket.WebSocketError, IOError) as ex:
            await system_logger.debug(
                message=_local_("Ws write error."), description=(str(ex))
            )

    async def close_with_msg(self, msg, code=4001):
        await self.write_msg(msg)
        self.close(code=code, reason=msg)

    # unused abstract method implementation
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass
