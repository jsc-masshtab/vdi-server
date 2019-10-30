# -*- coding: utf-8 -*-
from cached_property import cached_property
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from tornado.escape import json_decode

from settings import VEIL_REQUEST_TIMEOUT, VEIL_CONNECTION_TIMEOUT, VEIL_MAX_BODY_SIZE, VEIL_MAX_CLIENTS
from common.veil_errors import NotFound, Unauthorized, ServerError, Forbidden, ControllerNotAccessible, BadRequest
from controller.models import Controller
from common.veil_decorators import prepare_body
from controller.models import VeilCredentials

# TODO: Используется не tornado.curl_httpclient.CurlAsyncHTTPClient, потому что не измерен реальный прирост.
#  Есть подозрение, что ECP итак не справится.
AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient",
                          max_clients=VEIL_MAX_CLIENTS,
                          max_body_size=VEIL_MAX_BODY_SIZE)


class VeilHttpClient:
    """Abstract class for Veil ECP connection. Simply non-blocking HTTP(s) fetcher from remote Controller.
       response_types always json"""

    def __init__(self):
        self._client = AsyncHTTPClient()

    @cached_property
    async def headers(self):
        """controller ip-address must be set in the descendant class."""
        token = await Controller.get_token(self.controller_ip)
        headers = {
            'Authorization': 'jwt {}'.format(token),
            'Content-Type': 'application/json',
        }
        return headers

    @prepare_body
    async def fetch(self, url: str, method: str, body: str = ''):
        if method == 'GET' and not body:
            body = None
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
            print('http_error.code', http_error.code)
            if http_error.code == 400:
                # TODO: add response body parsing
                raise BadRequest(http_error.message)
            elif http_error.code == 401:
                raise Unauthorized()
            elif http_error.code == 403:
                raise Forbidden()
            elif http_error.code == 404:
                raise NotFound(url=url)
            elif http_error.code == 408:
                # TODO: add response body parsing
                raise ControllerNotAccessible()
            elif http_error.code == 500:
                # TODO: add response body parsing?
                raise ServerError()
        return response

    async def fetch_with_response(self, url: str, method: str, body: str = None):
        """Check response headers. Search json in content-type value"""
        response = await self.fetch(url, method, body)
        response_headers = response.headers
        response_content_type = response_headers.get('Content-Type')

        if not response_content_type:
            return

        if not isinstance(response_content_type, str):
            return

        if response_content_type.lower().find('json') == -1:
            raise NotImplementedError
        try:
            response = json_decode(response.body)
        except ValueError:
            response = dict()

        return response
