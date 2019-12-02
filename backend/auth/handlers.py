# -*- coding: utf-8 -*-
from abc import ABC

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import encode_jwt
from user.models import User
from auth.models import AuthenticationDirectory
# TODO: change User is invalid on INVALID_CREDENTIALS
# TODO: add proper exception


class AuthHandler(BaseHandler, ABC):
    async def post(self):
        try:
            if not self.args:
                raise AssertionError('Missing request body')
            if 'username' and 'password' not in self.args:
                raise AssertionError('Missing username and password')
            if self.args.get('ldap'):
                await AuthenticationDirectory.authenticate(self.args['username'], self.args['password'])
            else:
                password_is_valid = await User.check_user(self.args['username'], self.args['password'])
                if not password_is_valid:
                    raise AssertionError('Invalid credentials')
            access_token = encode_jwt(self.args['username'])
            await User.login(username=self.args['username'], token=access_token.get('access_token'))
            response = {"data": access_token}
        except AssertionError as E:
            response = {'errors': [str(E)]}
        return self.finish(response)


# Сейчас функционал обновления токена не реализован на клиенте.
# class RefreshAuthHandler(BaseHandler, ABC):
#     # TODO: не окончательная версия. Нужно решить, делаем как в ECP разрешая обновлять только
#     #  не истекшие времени или проверяем это по хранимому токену
#     def post(self):
#         try:
#             token_info = refresh_access_token(self.request.headers)
#         except:
#             self._transforms = []
#             self.set_status(401)
#             return self.finish('Token has expired.')
#         return self.finish(token_info)
