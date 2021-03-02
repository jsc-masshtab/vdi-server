# -*- coding: utf-8 -*-

import pytest
from tornado.testing import gen_test
from tornado.httpclient import HTTPClientError

from web_app.tests.utils import VdiHttpTestCase
from web_app.tests.fixtures import (
    fixt_db,
    fixt_user_locked,
    fixt_user,
    fixt_user_admin,
    fixt_auth_dir,  # noqa
    fixt_mapping,
    fixt_group,
    fixt_group_role,
)  # noqa

from common.languages import lang_init
from common.settings import LOCAL_AUTH, EXTERNAL_AUTH, PAM_AUTH


_ = lang_init()

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.auth,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


class AuthLocalTestCase(VdiHttpTestCase):
    def check_local_auth(self, response_dict: dict):
        """Если локальная авторизация отключена - ожидаем ошибку."""
        if not LOCAL_AUTH:
            error_message = response_dict["errors"][0]["message"]
            self.assertIn("Ошибка авторизации пользователя:", error_message)

    @pytest.mark.usefixtures("fixt_db", "fixt_user_admin")
    @gen_test
    def test_local_auth_ok(self):
        body = '{"username": "test_user_admin","password": "veil"}'
        response_dict = yield self.get_response(body=body)
        self.check_local_auth(response_dict)
        if LOCAL_AUTH:
            access_token = response_dict["data"]["access_token"]
            self.assertTrue(access_token)

    @pytest.mark.usefixtures("fixt_db")
    @gen_test
    def test_local_auth_bad(self):
        body = '{"username": "test_user_admin","password": "qwe11"}'
        response_dict = yield self.get_response(body=body)
        self.check_local_auth(response_dict)
        if LOCAL_AUTH:
            error_message = response_dict["errors"][0]["message"]
            self.assertIn(
                "Ошибка авторизации пользователя: test_user_admin.", error_message
            )

    @pytest.mark.usefixtures("fixt_db", "fixt_user_locked")
    @gen_test
    def test_locked_user_login(self):
        body = '{"username": "test_user_locked","password": "qwe"}'
        response_dict = yield self.get_response(body=body)
        error_message = response_dict["errors"][0]["message"]
        self.assertIn(
            "Ошибка авторизации пользователя: test_user_locked.", error_message
        )

    @pytest.mark.usefixtures("fixt_db")
    @gen_test
    def test_user_login_without_pass(self):
        body = '{"username": "test_user_admin","password": ""}'
        response_dict = yield self.get_response(body=body)
        error_message = response_dict["errors"][0]["message"]
        self.assertIn(
            "Ошибка авторизации пользователя: test_user_admin.", error_message
        )

    @pytest.mark.usefixtures("fixt_db", "fixt_user", "fixt_user_admin")
    @gen_test
    def test_blocked_section_admin_access(self):
        body = '{"username": "test_user_admin","password": "veil"}'
        response_dict = yield self.get_response(body=body)
        self.check_local_auth(response_dict)
        if LOCAL_AUTH:
            access_token = response_dict["data"]["access_token"]
            self.assertTrue(access_token)
            body = '{"query":"query {users {username, is_superuser, is_active}}"}'
            headers = {
                "Content-Type": "application/json",
                "Authorization": "jwt {}".format(access_token),
            }
            response_dict = yield self.get_response(
                body=body, url="/users", headers=headers
            )
            self.assertTrue(response_dict["data"]["users"])

            body = '{"username": "test_user","password": "veil"}'
            response_dict = yield self.get_response(body=body)
            access_token = response_dict["data"]["access_token"]
            self.assertTrue(access_token)

            headers = {
                "Content-Type": "application/json",
                "Authorization": "jwt {}".format(access_token),
            }
            body = '{"query":"query {users {username, is_superuser, is_active}}"}'
            response_dict = yield self.get_response(
                body=body, url="/users", headers=headers
            )
            error_message = response_dict["errors"][0]["message"]
            self.assertIn(_("Invalid permissions."), error_message)

    @pytest.mark.usefixtures("fixt_db", "fixt_user")
    @gen_test
    def test_logout(self):
        # Выполняем вход
        body = '{"username": "test_user","password": "veil"}'
        response_dict = yield self.get_response(body=body)
        self.check_local_auth(response_dict)
        if LOCAL_AUTH:
            access_token = response_dict["data"]["access_token"]
            headers_auth = {
                "Content-Type": "application/json",
                "Authorization": "jwt {}".format(access_token),
            }

            # Выполняем выход
            response = yield self.fetch_request(
                url="/logout", headers=headers_auth, body=""
            )
            self.assertEqual(response.code, 200)

            # Проверяем доступность закрытого раздела
            try:
                yield self.fetch_request(
                    url="/users", body='{"query":"{users{id}}"}', headers=headers_auth
                )
            except HTTPClientError as http_error:
                self.assertEqual(http_error.code, 401)
            else:
                self.assertTrue(False)


class AuthLdapTestCase(VdiHttpTestCase):
    def check_external_auth(self, response_dict: dict):
        """Если внешняя авторизация отключена - ожидаем ошибку."""
        if not EXTERNAL_AUTH:
            error_message = response_dict["errors"][0]["message"]
            self.assertIn("Ошибка авторизации пользователя:", error_message)

    @pytest.mark.usefixtures("fixt_db", "fixt_user")
    @gen_test
    def test_ldap_auth_no_controller(self):
        body = '{"username": "test_user","password": "veil", "ldap": true}'
        response_dict = yield self.get_response(body=body)
        self.check_external_auth(response_dict)
        if EXTERNAL_AUTH:
            error_message = response_dict["errors"][0]["message"]
            self.assertIn("Ошибка авторизации пользователя: test_user.", error_message)

    @pytest.mark.usefixtures("fixt_db", "fixt_auth_dir", "fixt_user")
    @gen_test
    def test_ldap_auth_ok(self):
        body = '{"username": "ad120", "password": "Bazalt1!", "ldap": true}'
        response_dict = yield self.get_response(body=body)
        self.check_external_auth(response_dict)
        if EXTERNAL_AUTH:
            access_token = response_dict["data"]["access_token"]
            self.assertTrue(access_token)

    @pytest.mark.usefixtures("fixt_db", "fixt_auth_dir", "fixt_user")
    @gen_test
    def test_ldap_auth_bad(self):
        body = '{"username": "test_user","password": "veil", "ldap": true}'
        response_dict = yield self.get_response(body=body)
        self.check_external_auth(response_dict)
        if EXTERNAL_AUTH:
            error_message = response_dict["errors"][0]["message"]
            self.assertIn("Ошибка авторизации", error_message)

    @pytest.mark.usefixtures(
        "fixt_db", "fixt_auth_dir", "fixt_group", "fixt_mapping", "fixt_group_role"
    )
    @gen_test
    def test_user_mapping(self):
        """Проверяем назначена ли пользователю группа после входа."""
        body = '{"username": "ad120", "password": "Bazalt1!", "ldap": true}'
        response_dict = yield self.get_response(body=body)
        self.check_external_auth(response_dict)
        if EXTERNAL_AUTH:
            access_token = response_dict["data"]["access_token"]
            self.assertTrue(access_token)

            body = '{"query":"query {users {username, is_superuser, is_active}}"}'
            headers = {
                "Content-Type": "application/json",
                "Authorization": "jwt {}".format(access_token),
            }
            response_dict = yield self.get_response(
                body=body, url="/users", headers=headers
            )
            response_message = response_dict["data"]["users"]
            self.assertTrue(response_message)
