# -*- coding: utf-8 -*-
from abc import ABC
import json
import asyncio
import uuid

from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.graphql import graphql
from tornado.testing import AsyncHTTPTestCase
from tornado.ioloop import IOLoop
from tornado.escape import json_decode

from web_app.auth.license.utils import License, LicenseData
from web_app.app import make_app

from common.subscription_sources import WsMessageType


class ExecError(Exception):
    pass


async def execute_scheme(_schema, query, variables=None, context=None):
    r = await graphql(
        _schema,
        query,
        variable_values=variables,
        executor=AsyncioExecutor(),
        return_promise=True,
        context_value=context,
    )
    if r.errors:
        raise ExecError(repr(r.errors))
    return r.data


async def ws_wait_for_text_msg(ws_conn, msg_type=WsMessageType.TEXT_MSG.value):

    while True:
        msg = await ws_conn.read_message()
        msg_dict = json.loads(msg)
        if msg_dict["msg_type"] == msg_type:
            return msg_dict


async def ws_wait_for_text_msg_with_timeout(ws_conn, msg_type=WsMessageType.TEXT_MSG.value):

    msg_wait_timeout = 3
    msg_dict = await asyncio.wait_for(
        ws_wait_for_text_msg(ws_conn, msg_type), msg_wait_timeout
    )
    return msg_dict


class VdiHttpTestCase(AsyncHTTPTestCase):

    @staticmethod
    def init_fake_license(expired: bool = False):
        current_license = License()
        if expired:
            license_data = {
                "verbose_name": "Fake license",
                "thin_clients_limit": 10,
                "uuid": str(uuid.uuid4()),
                "expiration_date": "2020-05-01",
                "support_expiration_date": "2020-05-01"
            }
        else:
            license_data = {
                "verbose_name": "Fake license",
                "thin_clients_limit": 10,
                "uuid": str(uuid.uuid4()),
                "expiration_date": "2030-05-01",
                "support_expiration_date": "2030-05-01"
            }
        current_license.license_data = LicenseData(**license_data)

    def get_app(self):
        self.init_fake_license()
        return make_app()

    def get_new_ioloop(self):
        return IOLoop.current()

    async def do_login(self, user_name="test_user_admin", password="veil"):
        body = {"username": user_name, "password": password}
        response_dict = await self.get_response(body=json.dumps(body))
        access_token = response_dict["data"]["access_token"]
        self.assertTrue(access_token)

        return user_name, access_token

    async def get_auth_headers(self, username: str = "test_user_admin",
                               password: str = "veil") -> dict:
        """Заголовки для подключения к брокеру."""
        (user_name, access_token) = await self.do_login(user_name=username,
                                                        password=password)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "jwt {}".format(access_token),
        }
        return headers

    async def fetch_request(self, body, url, headers, method="POST"):
        if not headers:
            headers = {"Content-Type": "application/json"}
        return await self.http_client.fetch(
            self.get_url(url), method=method, body=body, headers=headers
        )

    async def get_response(self,
                           body,
                           url="/auth",
                           headers=None,
                           method="POST"):
        response = await self.fetch_request(
            body=body, url=url, headers=headers, method=method
        )
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        return response_dict
