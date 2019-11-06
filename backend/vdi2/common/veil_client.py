# -*- coding: utf-8 -*-
from datetime import datetime

from cached_property import cached_property
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from tornado.escape import json_decode

from settings import VEIL_REQUEST_TIMEOUT, VEIL_CONNECTION_TIMEOUT, VEIL_MAX_BODY_SIZE, VEIL_MAX_CLIENTS
from common.veil_errors import NotFound, Unauthorized, ServerError, Forbidden, ControllerNotAccessible, BadRequest
from controller.models import Controller
from common.veil_decorators import prepare_body

# TODO: добавить обработку исключений
# TODO: Не tornado.curl_httpclient.CurlAsyncHTTPClient, т.к. не измерен реальный прирост производительности.

AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient",
                          max_clients=VEIL_MAX_CLIENTS,
                          max_body_size=VEIL_MAX_BODY_SIZE)


class VeilHttpClient:
    """Abstract class for Veil ECP connection. Simply non-blocking HTTP(s) fetcher from remote Controller.
       response_types always json"""

    def __init__(self, controller_ip: str):
        """Use create instead of init."""
        self._client = AsyncHTTPClient()
        self.controller_ip = controller_ip
        self.controller_uid = None

    @cached_property
    def based_url(self):
        return 'http://{}/api/'.format(self.controller_ip)

    @classmethod
    async def create(cls, controller_ip: str):
        """Because of we need async execute db query"""
        self = cls(controller_ip)
        self.controller_uid = await Controller.get_controller_id_by_ip(controller_ip)
        return self

    # @cached_property
    @property
    async def headers(self):
        """controller ip-address must be set in the descendant class."""
        token = await Controller.get_token(self.controller_uid)
        if not token:
            token = await self.login()
        headers = {
            'Authorization': 'jwt {}'.format(token),
            'Content-Type': 'application/json',
        }
        return headers

    async def login(self):
        """Авторизация c моделью."""

        auth_info = await Controller.get_auth_info(self.controller_uid)
        token, expires_on = await self.auth(auth_info)
        await Controller.set_auth_info(self.controller_uid, token, expires_on)
        return token

    async def auth(self, auth_info):
        """Авторизация на контроллере и получение токена."""

        method = 'POST'
        headers = {'Content-Type': 'application/json'}
        url = 'http://{}/auth/'.format(self.controller_ip)
        response = await self.fetch_with_response(url=url, method=method, headers=headers, body=auth_info)
        token = response.get('token')
        expires_on = datetime.strptime(response.get('expires_on'), "%d.%m.%Y %H:%M:%S UTC")
        if not token or not expires_on:
            raise AssertionError('Auth failed.')
        return token, expires_on

    @prepare_body
    async def fetch(self, url: str, method: str, headers: dict = None, body: str = ''):
        if method == 'GET' and body == '':
            body = None
        if not headers:
            headers = await self.headers
        try:
            request = HTTPRequest(url=url,
                                  method=method,
                                  headers=headers,
                                  body=body,
                                  connect_timeout=VEIL_CONNECTION_TIMEOUT,
                                  request_timeout=VEIL_REQUEST_TIMEOUT)
            response = await self._client.fetch(request)
        except HTTPClientError as http_error:
            body = self.get_response_body(http_error.response)
            if http_error.code == 400:
                raise BadRequest(body)
            elif http_error.code == 401:
                await Controller.invalidate_auth(self.controller_uid)
                raise Unauthorized()
            elif http_error.code == 403:
                raise Forbidden(body)
            elif http_error.code == 404:
                raise NotFound(url=url)
            elif http_error.code == 408:
                raise ControllerNotAccessible(body)
            elif http_error.code == 500:
                raise ServerError(body)
        return response

    @staticmethod
    def get_response_body(response):
        response_headers = response.headers
        response_content_type = response_headers.get('Content-Type')

        if not isinstance(response_content_type, str):
            return AssertionError('Can\'t process Content-Type.')

        if response_content_type.lower().find('json') == -1:
            raise NotImplementedError('Only \'json\' Content-Type.')
        try:
            response = json_decode(response.body)
        except ValueError:
            response = dict()
        return response

    async def fetch_with_response(self, url: str, method: str, headers: dict = None, body: str = None):
        """Check response headers. Search json in content-type value"""
        response = await self.fetch(url=url, method=method, headers=headers, body=body)
        response_body = self.get_response_body(response)
        return response_body

