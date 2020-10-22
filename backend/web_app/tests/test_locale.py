# -*- coding: utf-8 -*-

import pytest
from tornado.testing import gen_test

from web_app.tests.utils import VdiHttpTestCase
from web_app.tests.fixtures import fixt_db, fixt_user  # noqa

from common.settings import LANGUAGE

pytestmark = [pytest.mark.asyncio, pytest.mark.auth]


class AuthTestLocale(VdiHttpTestCase):

    @pytest.mark.usefixtures('fixt_db', 'fixt_user')
    @gen_test
    def test_locale_auth_without_password(self):
        body = '{"username": "test_user","password": "!", "ldap": true}'  # Пропущен пароль!
        response_dict = yield self.get_response(body=body)
        error_message = response_dict['errors'][0]['message']
        if LANGUAGE == 'en':
            self.assertIn('Missing password.', error_message)
        elif LANGUAGE == 'ru':
            self.assertIn('Отсутствует пароль.', error_message)
