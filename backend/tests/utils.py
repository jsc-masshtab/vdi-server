# -*- coding: utf-8 -*-
from abc import ABC

from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.graphql import graphql
from tornado.testing import AsyncHTTPTestCase
from tornado.ioloop import IOLoop
from tornado.escape import json_decode

from app import make_app


class ExecError(Exception):
    pass


async def execute_scheme(_schema, query, variables=None, context=None):
    r = await graphql(_schema, query, variables=variables, executor=AsyncioExecutor(), return_promise=True,
                      context=context)
    if r.errors:
        raise ExecError(repr(r.errors))
    return r.data


class VdiHttpTestCase(AsyncHTTPTestCase, ABC):
    method = 'POST'

    def get_app(self):
        return make_app()

    def get_new_ioloop(self):
        return IOLoop.current()

    async def fetch_request(self, body, url, headers):
        if not headers:
            headers = {'Content-Type': 'application/json'}
        return await self.http_client.fetch(self.get_url(url),
                                            method=self.method,
                                            body=body,
                                            headers=headers)

    async def get_response(self, body: dict, url='/auth', headers=None):
        response = await self.fetch_request(body=body, url=url, headers=headers)
        self.assertEqual(response.code, 200)
        response_dict = json_decode(response.body)
        self.assertIsInstance(response_dict, dict)
        return response_dict
