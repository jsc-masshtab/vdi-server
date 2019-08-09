import time
import urllib
from contextlib import asynccontextmanager
from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async import Task as _Task, TaskTimeout, wait
from vdi.errors import WsTimeout, FetchException, ControllerNotAccessible, AuthError, SimpleError
from vdi.utils import with_self
from vdi.settings import settings
from vdi.tasks.client import HttpClient


class Task(_Task):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, FetchException):
            self.on_fetch_failed(exc_val, exc_val.http_error.code)
            return True

    @with_self
    async def run(self):
        # Implementation here
        raise NotImplementedError

    def on_fetch_failed(self, ex, code):
        raise ex





@dataclass()
class Token(Task):
    controller_ip: str

    creds = settings.credentials

    @cached
    def url(self):
        return f'http://{self.controller_ip}/auth/'

    @with_self
    async def run(self):
        http_client = HttpClient()
        params = urllib.parse.urlencode(self.creds)
        response = await http_client.fetch(self.url, method='POST', body=params)
        return response['token']

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise ControllerNotAccessible(ip=self.controller_ip)
        if code == 400:
            if ex.data['non_field_errors'] == [AuthError.message]:
                raise AuthError()
        raise ex


class UrlFetcher(Task):

    async def headers(self):
        token = await Token(controller_ip=self.controller_ip)
        return {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }

    @cached
    def client(self):
        return HttpClient()

    def __repr__(self):
        return repr(self.client)

    @with_self
    async def run(self):
        return await self.client.fetch_using(self)

    async def wait_message(self, ws):
        try:
            return await ws.wait_message(self.is_done)
        except TaskTimeout:
            raise WsTimeout(url=self.url, data="Таймаут ожидания завершения")


class DiscoverController(UrlFetcher):

    async def discover_and_run(self):
        assert self.controller_ip is None
        params = {
            key: getattr(self, key)
            for key in self.__dataclass_fields__.keys()
        }
        from vdi.tasks.resources import DiscoverControllers
        tasks = {
            co['ip']: self.__class__(**{**params, 'controller_ip': co['ip']})
            for co in await DiscoverControllers()
        }
        async for controller_ip, result in wait(**tasks).items():
            if not isinstance(result, Exception):
                return result, controller_ip
        raise SimpleError(f'Автоопределение контроллера не удалось: {self.__class__.__name__}')

    async def run(self):
        if self.controller_ip:
            return await super().run()
        return await self.discover_and_run()