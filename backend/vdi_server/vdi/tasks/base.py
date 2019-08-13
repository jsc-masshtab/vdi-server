from __future__ import annotations
import time
import urllib
from contextlib import asynccontextmanager
from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async import Task as _Task, TaskTimeout, wait, g
from vdi.errors import WsTimeout, FetchException, ControllerNotAccessible, AuthError, SimpleError
from vdi.utils import with_self
from vdi.settings import settings
from vdi.tasks.client import HttpClient

from vdi.db import db




@dataclass()
class TaskContextManager:
    task: Task

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, FetchException):
            self.task.on_fetch_failed(exc_val, exc_val.http_error.code)
            return True


class ErrorHandler(_Task):
    rerun_cause: str = None

    def needs_rerun(self, cause: str):
        self.rerun_cause = cause

    def on_fetch_failed(self, ex, code):
        raise ex

    def co(self):
        return self.run_and_handle()

    async def run_and_handle(self):
        run = super().co()
        ctx = TaskContextManager(self)
        with ctx:
            result = await run
        while self.rerun_cause:
            rerun_cause = self.rerun_cause
            self.rerun_cause = None
            with ctx:
                result = await self.rerun(rerun_cause)

        return result


class Task(ErrorHandler, _Task):

    async def run(self):
        # Implementation here
        raise NotImplementedError

    async def rerun(self):
        raise NotImplementedError



@dataclass()
class Token(Task):
    controller_ip: str

    creds = settings.credentials

    @cached
    def url(self):
        return f'http://{self.controller_ip}/auth/'

    async def run(self):
        async with db.connect() as conn:
            qu = 'select token from veil_creds where username = $1', self.creds['username']
            data = await conn.fetch(*qu)
            print('from db')
            # TODO expiration
            [[token]] = data
            if token:
                return token
        if db.cache.get('token'):
            return db.cache['token']
        http_client = HttpClient()
        params = urllib.parse.urlencode(self.creds)
        response = await http_client.fetch(self.url, method='POST', body=params)
        token = response['token']
        async with db.connect() as conn:
            qu = 'update veil_creds set token=$1 where username = $2', token, self.creds['username']
            await conn.execute(*qu)
        db.cache['token'] = token
        return token

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise ControllerNotAccessible(ip=self.controller_ip)
        if code == 400:
            if ex.data['non_field_errors'] == [AuthError.message]:
                raise AuthError()
        raise ex


@dataclass()
class RefreshToken(Task):
    controller_ip: str

    async def run(self):
        token = await Token(controller_ip=self.controller_ip)
        url = f'http://{self.controller_ip}/auth/'
        body = urllib.parse.urlencode({'token': token})
        http_client = HttpClient()
        response = await http_client.fetch(url, method='POST', body=body)
        return response['token']


class UrlFetcher(Task):


    async def headers(self):
        token = await Token(controller_ip=self.controller_ip)
        return {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }

    def on_fetch_failed(self, ex, code):
        raise ex
        # if ex.code == 401:
        #     self.needs_rerun('refresh_token')

    @cached
    def client(self):
        return HttpClient()

    def __repr__(self):
        return repr(self.client)

    async def run(self):
        return await self.client.fetch_using(self)

    # async def rerun(self, cause):
    #     if cause == 'refresh_token':
    #         await RefreshToken(self.controller_ip)
    #         g.init()
    #         return await self.run()
    #     raise NotImplementedError


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