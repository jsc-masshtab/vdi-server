# -*- coding: utf-8 -*-
from abc import ABC

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import encode_jwt, extract_user_and_token_with_no_expire_check
from user.models import User
from auth.models import AuthenticationDirectory
from event.models import Event


class AuthHandler(BaseHandler, ABC):

    async def post(self):
        try:
            if not self.args:
                raise AssertionError('Missing request body')
            if 'username' and 'password' not in self.args:
                raise AssertionError('Missing username and password')

            username = self.args['username']
            password = self.args['password']
            if not username or len(username) < 2:
                raise AssertionError('Missing username')
            if not password or len(password) < 2:
                raise AssertionError('Missing password')

            if self.args.get('ldap'):
                await AuthenticationDirectory.authenticate(self.args['username'], self.args['password'])
            else:
                password_is_valid = await User.check_user(self.args['username'], self.args['password'])
                if not password_is_valid:
                    raise AssertionError('Invalid credentials')

            access_token = encode_jwt(self.args['username'])
            await User.login(username=self.args['username'], token=access_token.get('access_token'), ip=self.remote_ip,
                             ldap=self.args.get('ldap'), client_type=self.client_type)
            response = {'data': access_token}
        except AssertionError as E:
            error = str(E)
            response = {'errors': [{'message': error}]}

            error_message = 'Authentication failed: {err}'.format(err=error)
            if self.args.get('username'):
                error_message += ' for user {username}'.format(username=self.args['username'])
            error_message += '. IP address: {ip}'.format(ip=self.remote_ip)
            entity_list = [
                {'entity_type': 'Security', 'entity_uuid': None},
                {'entity_type': self.client_type, 'entity_uuid': None}
            ]
            await Event.create_warning(error_message, entity_list=entity_list)
        return self.finish(response)


class LogoutHandler(BaseHandler, ABC):
    async def post(self):
        username, token = extract_user_and_token_with_no_expire_check(self.request.headers)
        await User.logout(username=username, access_token=token)


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
