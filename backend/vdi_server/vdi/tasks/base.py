from __future__ import annotations

import inspect

from dateutil.parser import parse as parse_dt

from datetime import datetime, timedelta, timezone
import time
import urllib
from contextlib import asynccontextmanager, contextmanager, AsyncExitStack, ExitStack
from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async import Task as _Task, TaskTimeout, wait, g
from vdi.errors import WsTimeout, FetchException, ControllerNotAccessible, AuthError, SimpleError, SignatureExpired
from vdi.settings import settings
from vdi.tasks.client import HttpClient

from vdi.db import db, fetch
from vdi import lock
from vdi.utils import Unset


class ErrorHandler(_Task):
    _result = Unset

    def on_fetch_failed(self, ex, code):
        raise ex

    def on_error(self, ex):
        raise ex

    def set_result(self, value):
        self._result = value

    ERROR_HANDLERS = ['on_error', 'on_fetch_failed']

    def get_error_handler_type(self):
        is_sync = is_async = False
        for name in self.ERROR_HANDLERS:
            method = getattr(self, name, None)
            if inspect.iscoroutinefunction(method):
                is_async = True
            else:
                is_sync = True
        if is_sync and not is_async:
            return 'sync'
        if is_async and not is_sync:
            return 'async'
        assert not 'allowed both sync and async handlers'

    @asynccontextmanager
    async def async_catch_errors(self):
        try:
            yield
        except BaseException as ex:
            if isinstance(ex, FetchException):
                await self.on_fetch_failed(ex, ex.http_error.code)
            else:
                await self.on_error(ex)

    @contextmanager
    def catch_errors(self):
        try:
            yield
        except BaseException as ex:
            if isinstance(ex, FetchException):
                self.on_fetch_failed(ex, ex.http_error.code)
            else:
                self.on_error(ex)

    async def run(self):
        handler_type = self.get_error_handler_type()
        if handler_type == 'sync':
            with self.catch_errors():
                return await super().co()
        elif handler_type == 'async':
            async with self.async_catch_errors():
                return await super().co()
        if self._result is not Unset:
            return self._result


class Task(ErrorHandler, _Task):

    async def run(self):
        # Implementation here
        raise NotImplementedError


@dataclass()
class FetchToken(Task):
    controller_ip: str

    creds = settings.credentials

    @property
    def url(self):
        return f'http://{self.controller_ip}/auth/'

    async def run(self):
        http_client = HttpClient()
        params = urllib.parse.urlencode(self.creds)
        data = await http_client.fetch(self.url, method='POST', body=params)
        expires_on = parse_dt(data['expires_on'])
        return data['token'], expires_on

    def on_fetch_failed(self, ex, code):
        if code == 404:
            raise ControllerNotAccessible(ip=self.controller_ip) from ex
        if code == 400:
            if ex.data['non_field_errors'] == [AuthError.message]:
                raise AuthError() from ex
        raise ex



@dataclass()
class Token(Task):
    controller_ip: str

    @property
    def username(self):
        return settings.credentials['username']

    async def fetch_token_from_db(self):
        qu = 'select token from veil_creds where username = $1 and controller_ip = $2', \
             self.username, self.controller_ip
        token = await fetch(*qu)
        if token:
            [[token]] = token
            return token

    async def try_token(self, token):
        try:
            await CheckConnection(controller_ip=self.controller_ip, token=token)
            return True
        except SignatureExpired:
            return False
        except BaseException:
            breakpoint()

    async def run(self):
        token = await self.fetch_token_from_db()
        if token:
            if await self.try_token(token):
                return token
        async with lock.token:
            # have to check the db for the token again:
            # maybe it has been fetched while we've been waiting to aquire the lock
            old_token = token
            token = await self.fetch_token_from_db()
            if token != old_token:
                return token
            token, expires_on = await FetchToken(controller_ip=self.controller_ip)
            async with db.connect() as conn:
                qu = (
                    'insert into veil_creds (username, controller_ip, token, expires_on) '
                    'values ($1, $2, $3, $4) '
                    'on conflict on constraint veil_creds_pk do update '
                    'set token = excluded.token, expires_on = excluded.expires_on',
                    self.username, self.controller_ip, token, expires_on
                )
                await conn.execute(*qu)

            return token



# unused
@dataclass()
class RefreshToken(Task):
    controller_ip: str
    token: str

    async def run(self):
        url = f'http://{self.controller_ip}/refresh-token/'
        body = urllib.parse.urlencode({'token': self.token})
        http_client = HttpClient()
        data = await http_client.fetch(url, method='POST', body=body)
        return data['token'], data['expires_on']

    # def on_fetch_failed(self, ex, code):
    #     if code == SignatureExpired.code and ex.data['non_field_errors'] == [SignatureExpired.message]:
    #         await

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

    async def wait_message(self, ws):
        try:
            return await ws.wait_message(self.is_done)
        except TaskTimeout:
            raise WsTimeout(url=self.url, data="Таймаут ожидания завершения")


@dataclass()
class CheckConnection(UrlFetcher):
    controller_ip: str
    token: str = None

    async def headers(self):
        if self.token:
            token = self.token
        else:
            token = await Token(controller_ip=self.controller_ip)
        return {
            'Authorization': f'jwt {token}',
            'Content-Type': 'application/json',
        }

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/controllers/system-time"

    def on_fetch_failed(self, ex, code):
        breakpoint()
        if code == SignatureExpired.code and ex.data['non_field_errors'] == [SignatureExpired.message]:
            raise SignatureExpired()
        raise ControllerNotAccessible(ip=self.controller_ip) from ex



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