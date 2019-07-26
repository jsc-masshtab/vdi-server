import urllib
from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async import Task as _Task, TaskTimeout
from vdi.errors import WsTimeout, FetchException, ControllerNotAccessible, AuthError
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


@dataclass()
class UrlFetcher(Task):
    controller_ip: str

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

