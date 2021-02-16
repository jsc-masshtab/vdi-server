# -*- coding: utf-8 -*-
from typing import Optional, Awaitable
from tornado import websocket

from common.models.auth import UserJwtInfo
from common.veil.auth.veil_jwt import decode_jwt

from common.log.journal import system_logger
from common.languages import lang_init

_ = lang_init()


class BaseWsHandler(websocket.WebSocketHandler):

    def check_origin(self, origin):
        # TODO: временное решение
        return True

    async def _validate_token(self):
        """Проверить токен. Вернуть token, если валидация прошла. Иначе None"""
        try:
            token = self.get_query_argument('token')
            if not token:
                raise AssertionError('Jwt token must be send as query param')
            if token and 'jwt' in token:
                token = token.replace('jwt', '')
            token = token.replace(' ', '')

            # token checking
            payload = decode_jwt(token)
            payload_user = payload.get('username')
            is_valid = await UserJwtInfo.check_token(payload_user, token)
            if not is_valid:
                raise AssertionError('Auth failed. Wrong jwt token')

            return token

        except Exception as ex:  # noqa
            await self._write_msg('Token validation error. {}.'.format(str(ex)))
            self.close()
            return None

    async def _write_msg(self, msg):
        try:
            await self.write_message(msg)
        except websocket.WebSocketError:
            await system_logger.debug(_('Write error.'))

    # unused abstract method implementation
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass
