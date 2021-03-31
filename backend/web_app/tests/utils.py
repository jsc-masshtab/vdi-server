# -*- coding: utf-8 -*-
from abc import ABC
import json
import asyncio

from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.graphql import graphql
from tornado.testing import AsyncHTTPTestCase
from tornado.ioloop import IOLoop
from tornado.escape import json_decode

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


class VdiHttpTestCase(AsyncHTTPTestCase, ABC):
    async def do_login(self, user_name="test_user_admin", password="veil"):
        body = {"username": user_name, "password": password}
        response_dict = await self.get_response(body=json.dumps(body))
        access_token = response_dict["data"]["access_token"]
        self.assertTrue(access_token)

        return user_name, access_token

    def get_app(self):
        return make_app()

    def get_new_ioloop(self):
        return IOLoop.current()

    async def fetch_request(self, body, url, headers, method="POST"):
        if not headers:
            headers = {"Content-Type": "application/json"}
        return await self.http_client.fetch(
            self.get_url(url), method=method, body=body, headers=headers
        )

    async def get_response(self, body: dict, url="/auth", headers=None, method="POST"):
        response = await self.fetch_request(
            body=body, url=url, headers=headers, method=method
        )
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        return response_dict

    async def generate_headers_for_tk(self, user_name="test_user_admin", password="veil"):
        # Авторизуемся, чтобы получить токен
        (_, access_token) = await self.do_login(user_name, password)

        # Формируем данные для тестируемого параметра
        headers = {
            "Content-Type": "application/json",
            "Authorization": "jwt {}".format(access_token),
        }
        return headers
