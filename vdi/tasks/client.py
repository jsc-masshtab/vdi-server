import json
import inspect
from tornado.httpclient import HTTPRequest
from tornado.httpclient import AsyncHTTPClient

# TODO logging

class FetchException:
    'TODO'

class HttpClient:

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
        url = dic.pop('url')
        response = await self._client.fetch(url, **dic)
        if self._json:
            response = json.loads(response.body)
        return response

