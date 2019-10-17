# -*- coding: utf-8 -*-
from abc import ABC
from tornado import gen

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import get_jwt
from auth.models import User


class AuthHandler(BaseHandler, ABC):

    @gen.coroutine
    def post(self):
        if not self.args:
            # TODO: add proper exception
            print('Missing request body')
            return False
        if 'username' and 'password' not in self.args:
            # TODO: add proper exception
            print('Missing username and password')
            return False
        password_is_valid = yield User.check_user(self.args['username'], self.args['password'])

        if not password_is_valid:
            # TODO: add proper exception
            print('invalid password')
            return False

        token = get_jwt(self.args['username'])
        self.write(token)

