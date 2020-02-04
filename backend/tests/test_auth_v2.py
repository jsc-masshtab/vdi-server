# -*- coding: utf-8 -*-
"""Auth tests
   Надо убедиться, что в рабочей БД нет контроллера АД, либо сменить ему статус на время тестов.
"""

import pytest
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.httpclient import HTTPClientError
import tornado.ioloop
from tornado.escape import json_decode

from settings import (DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST,
                      TESTS_AD_DOMAIN_NAME, TESTS_AD_DIRECTORY_URL, TESTS_AD_VERBOSE_NAME,
                      TESTS_ADMIN_USERNAME, TESTS_ADMIN_PASSWORD,
                      TESTS_LDAP_USERNAME, TESTS_LDAP_PASSWORD)
from database import db
from app import app

from auth.models import AuthenticationDirectory, User, Event

pytestmark = [pytest.mark.asyncio, pytest.mark.auth]


class AuthTestCase(AsyncHTTPTestCase):
    method = 'POST'

    async def fetch_request(self, body, url='/auth', headers=None):
        if not headers:
            headers = {'Content-Type': 'application/json'}
        """В попытке уменьшить дублирование кода в тесте, вынес в отдельный метод."""
        return await self.http_client.fetch(self.get_url(url),
                                            method=self.method,
                                            body=body,
                                            headers=headers)

    def get_app(self):
        tornado.ioloop.IOLoop.current().run_sync(
            lambda: db.init_app(app,
                                host=DB_HOST,
                                port=DB_PORT,
                                user=DB_USER,
                                password=DB_PASS,
                                database=DB_NAME,
                                pool_max_size=100))
        return app

    @gen_test
    def test_local_auth_ok(self):
        body = '{"username": "%s","password": "%s"}' % (TESTS_ADMIN_USERNAME, TESTS_ADMIN_PASSWORD)
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['data']
        self.assertTrue(data.get('access_token'))
        mock_event = 'User {} has been logged in successfully.%'.format(TESTS_ADMIN_USERNAME)
        count = yield db.select([db.func.count()]).where((Event.event_type == Event.TYPE_INFO)
                                                         & (Event.message.like(mock_event))).gino.scalar()  # noqa
        self.assertTrue(count > 0)

    @gen_test
    def test_local_auth_bad(self):
        body = '{"username": "admin","password": "qwe11"}'
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['errors'][0]
        self.assertIn('Invalid credentials', data.get('message'))

    @gen_test
    def test_ldap_auth_no_controller(self):
        body = '{"username": "admin","password": "qwe", "ldap": true}'
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['errors'][0]
        self.assertIn('No authentication directory controllers', data.get('message'))

    @gen_test
    def test_ldap_auth_ok(self):
        # Не придуммал как это сделать через фикстуру, чтобы она удалилась. Надо поискать.
        yield AuthenticationDirectory.soft_create(verbose_name=TESTS_AD_VERBOSE_NAME, domain_name=TESTS_AD_DOMAIN_NAME,
                                                  directory_url=TESTS_AD_DIRECTORY_URL)
        body = '{"username": "%s","password": "%s", "ldap": true}' % (TESTS_LDAP_USERNAME, TESTS_LDAP_PASSWORD)
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['data']
        self.assertTrue(data.get('access_token'))
        auth_dir = yield AuthenticationDirectory.get_object(extra_field_name='verbose_name',
                                                            extra_field_value=TESTS_AD_VERBOSE_NAME)
        yield auth_dir.delete()
        user = yield User.get_object(extra_field_value=TESTS_LDAP_USERNAME, extra_field_name='username',
                                     include_inactive=True)
        yield user.delete()
        self.assertTrue(True)

    @gen_test
    def test_ldap_auth_bad(self):
        # Не придуммал как это сделать через фикстуру, чтобы она удалилась. Надо поискать.
        yield AuthenticationDirectory.soft_create(verbose_name=TESTS_AD_VERBOSE_NAME, domain_name=TESTS_AD_DOMAIN_NAME,
                                                  directory_url=TESTS_AD_DIRECTORY_URL)
        body = '{"username": "admin","password": "qwe", "ldap": true}'
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['errors'][0]
        self.assertIn('Invalid credeintials (ldap).', data.get('message'))
        auth_dir = yield AuthenticationDirectory.get_object(extra_field_name='verbose_name',
                                                            extra_field_value=TESTS_AD_VERBOSE_NAME)
        yield auth_dir.delete()
        self.assertTrue(True)

    @gen_test
    def test_locked_user_login(self):
        scope_username = 'TEST1111'
        user = yield User.soft_create(username=scope_username)
        yield user.deactivate()
        body = '{"username": "%s","password": "qweqwe"}' % scope_username
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['errors'][0]
        self.assertIn('Invalid credentials', data.get('message'))
        yield user.delete()
        self.assertTrue(True)

    @gen_test
    def test_user_login_with_bad_password(self):
        scope_username = 'TEST1111'
        user = yield User.soft_create(username=scope_username)
        body = '{"username": "%s","password": ""}' % scope_username
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['errors'][0]
        self.assertIn('Missing password', data.get('message'))
        yield user.delete()
        self.assertTrue(True)

    @gen_test
    def test_blocked_section_admin_access(self):
        body = '{"username": "%s","password": "%s"}' % (TESTS_ADMIN_USERNAME, TESTS_ADMIN_PASSWORD)
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['data']
        access_token = data['access_token']
        self.assertTrue(access_token)

        body = '{"query":"query {users {id, username, is_superuser, is_active}}"}'
        headers = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}
        response = yield self.fetch_request(body=body, url='/users', headers=headers)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['data']
        self.assertTrue(data['users'])

    @gen_test
    def test_blocked_section_admin_access_bad(self):
        user = yield User.soft_create(username='TEST1111', password='qwe123QQQ!')

        body = '{"username": "TEST1111","password": "qwe123QQQ!"}'
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['data']
        access_token = data['access_token']
        self.assertTrue(access_token)

        body = '{"query":"query {users {id, username, is_superuser, is_active}}"}'
        headers = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}
        response = yield self.fetch_request(body=body, url='/users', headers=headers)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)

        errors = response_dict['errors']
        error_message = errors[0].get('message')
        self.assertIn('Invalid permissions', error_message)

        yield user.delete()
        self.assertTrue(True)

    @gen_test
    def test_logout(self):
        # Выполняем вход
        body = '{"username": "%s","password": "%s"}' % (TESTS_ADMIN_USERNAME, TESTS_ADMIN_PASSWORD)
        response = yield self.fetch_request(body=body)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        data = response_dict['data']
        access_token = data['access_token']
        headers_auth = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}

        # Проверяем доступность закрытого раздела
        response = yield self.fetch_request(url='/users',
                                            body='{"query":"{users{id}}"}',
                                            headers=headers_auth)
        self.assertEqual(response.code, 200)

        # Выполняем выход
        response = yield self.fetch_request(url='/logout', headers=headers_auth, body='')
        self.assertEqual(response.code, 200)

        # Проверяем доступность закрытого раздела
        try:
            response = yield self.fetch_request(url='/users',
                                                body='{"query":"{users{id}}"}',
                                                headers=headers_auth)
        except HTTPClientError as http_error:
            self.assertEqual(http_error.code, 401)
        else:
            self.assertTrue(False)
