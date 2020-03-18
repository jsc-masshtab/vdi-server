# -*- coding: utf-8 -*-

import pytest
from tornado.testing import gen_test

from tests.utils import VdiHttpTestCase
from tests.fixtures import (fixt_db, fixt_user)  # noqa

from languages import lang_init


_ = lang_init()

pytestmark = [pytest.mark.asyncio, pytest.mark.auth]


class AuthTestLocale(VdiHttpTestCase):

    @pytest.mark.usefixtures('fixt_db', 'fixt_user')
    @gen_test
    def test_locale_auth_without_password(self):
        body = '{"username": "test_user","password": "!", "ldap": true}'  # Пропущен пароль
        response_dict = yield self.get_response(body=body)
        error_message = response_dict['errors'][0]['message']
        self.assertIn(_('Missing password'), error_message)
