# -*- coding: utf-8 -*-
from abc import ABC

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import get_jwt
from auth.models import User


class AuthHandler(BaseHandler, ABC):

    async def post(self):
        if not self.args:
            # TODO: add proper exception
            print('Missing request body')
            return
        if 'username' and 'password' not in self.args:
            # TODO: add proper exception
            print('Missing username and password')
            return
        password_is_valid = await User.check_user(self.args['username'], self.args['password'])

        if not password_is_valid:
            # TODO: add proper exception
            print('invalid password')
            await User.set_password(self.args['username'], self.args['password'])
            return

        token = get_jwt(self.args['username'])
        return self.finish(token)

