# -*- coding: utf-8 -*-

import pytest
from tornado.testing import gen_test

from tests.utils import VdiHttpTestCase
from tests.fixtures import (fixt_db, fixt_user_admin)  # noqa
from languages import lang_init

_ = lang_init()

pytestmark = [pytest.mark.asyncio, pytest.mark.license]


class LicenseTestCase(VdiHttpTestCase):

    @pytest.mark.usefixtures('fixt_db', 'fixt_user_admin')
    @gen_test
    def test_license_info(self):
        body = '{"username": "test_user_admin","password": "veil"}'
        response_dict = yield self.get_response(body=body, method='POST')
        access_token = response_dict['data']['access_token']
        self.assertTrue(access_token)

        headers = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}
        response_dict = yield self.get_response(body=None, url='/license', headers=headers, method='GET')

        self.assertIn('data', response_dict)
        data = response_dict['data']

        self.assertIn('expired', data)
        self.assertIn('support_remaining_days', data)
        self.assertIn('date_format', data)
        self.assertIn('remaining_days', data)
        self.assertIn('company', data)
        self.assertIn('verbose_name', data)
        self.assertIn('support_expired', data)
        self.assertIn('email', data)
        self.assertIn('thin_clients_limit', data)
        self.assertIn('expiration_date', data)
        self.assertIn('uuid', data)
        self.assertIn('support_expiration_date', data)

    @pytest.mark.usefixtures('fixt_db', 'fixt_user_admin')
    @gen_test
    def test_thin_client_redis_info(self):
        body = '{"username": "test_user_admin","password": "veil"}'
        response_dict = yield self.get_response(body=body, method='POST')
        access_token = response_dict['data']['access_token']
        self.assertTrue(access_token)

        headers = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}
        response_dict = yield self.get_response(body=None, url='/client/message_broker', headers=headers, method='GET')

        self.assertIn('data', response_dict)
        data = response_dict['data']
        print(data)
        self.assertIn('password', data)
        self.assertIn('db', data)
        self.assertIn('port', data)
        self.assertIn('channel', data)
