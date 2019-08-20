import socket
import sys

#TODO rename: we have client.py for thin client API

import json
import inspect
from tornado.httpclient import HTTPRequest, HTTPError
from tornado.httpclient import AsyncHTTPClient

from vdi.errors import FetchException, NotFound
from vdi.log import RequestsLog

MAX_BODY_SIZE = 10 * 1024 * 1024 * 1024

AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient",
                          max_body_size=MAX_BODY_SIZE,
                          )

class HttpClient:

    request_timeout = 24 * 3600

    def __init__(self, json=True):
        self._client = AsyncHTTPClient()
        self._json = json

    @classmethod
    def get_params(cls):
        sig = inspect.signature(HTTPRequest)
        return list(sig.parameters)

    @classmethod
    def get_essential_params(cls):
        '''
        These can be taken from namespace (attrs or methods)
        '''
        return [
            'url', 'method', 'body', 'headers',
        ]

    async def fetch_using(self, ns=None, **dic):
        '''
        fetch a resource using parameters from namespace ns
        '''
        all_params = set(self.get_params())
        dic = {
            k: v for k, v in dic.items()
            if k in all_params
        }
        for name in self.get_essential_params():
            if name in dic or ns is None:
                continue
            method = getattr(ns, name, None)
            if method is None:
                continue
            if inspect.iscoroutinefunction(method):
                dic[name] = await method()
            elif callable(method):
                dic[name] = method()
            else:
                # is actually an attribute
                dic[name] = method
        self._repr_obj = dict(dic)
        url = dic.pop('url')
        return await self.fetch(url, **dic)

    def __repr__(self):
        if hasattr(self, '_repr_obj'):
            return repr(self._repr_obj)
        return super().__repr__()

    def get_error_data(self, e: HTTPError):
        val = e.response.buffer.read()
        val = val.decode('utf-8')
        obj = json.loads(val)
        return obj

    async def fetch(self, *args, **kwargs):
        if not 'request_timeout' in kwargs:
            kwargs['request_timeout'] = self.request_timeout
        if 'url' in kwargs:
            url = kwargs['url']
        elif args:
            url = args[0]
        try:
            async with RequestsLog.log(url=url):
                response = await self._client.fetch(*args, **kwargs)
        except socket.gaierror as e:
            raise NotFound(url=url)
        except HTTPError as e:
            if e.code == 404:
                raise NotFound(url=url)
            data = self.get_error_data(e)
            if not isinstance(data, dict):
                data = {'detail': data}
            raise FetchException(url=url, http_error=e, data=data)
        if self._json:
            response = json.loads(response.body)
        return response

