# -*- coding: utf-8 -*-

import pytest
from tornado.testing import gen_test

from web_app.tests.utils import VdiHttpTestCase
from web_app.tests.fixtures import fixt_db, fixt_redis_client, fixt_user  # noqa
from common.settings import LANGUAGE, PAM_AUTH

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.auth,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


class AuthTestLocale(VdiHttpTestCase):
    @pytest.mark.usefixtures("fixt_db", "fixt_user")
    @gen_test
    def test_locale_auth_without_password(self):
        body = (
            '{"username": "test_user","password": "!", "ldap": true, "code": ""}'
        )  # Пропущен пароль!
        response_dict = yield self.get_response(body=body)
        error_message = response_dict["errors"][0]["message"]
        if LANGUAGE == "ru":
            self.assertIn("Ошибка авторизации пользователя: test_user.", error_message)
