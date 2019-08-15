from __future__ import annotations

from dateutil.parser import parse as parse_dt

from datetime import datetime, timedelta, timezone
import time
import urllib
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass

from cached_property import cached_property as cached
from classy_async import Task as _Task, TaskTimeout, wait, g
from vdi.errors import WsTimeout, FetchException, ControllerNotAccessible, AuthError, SimpleError
from vdi.settings import settings
from vdi.tasks.client import HttpClient

from vdi.db import db
from vdi import lock



class ErrorHandler(_Task):

    def on_fetch_failed(self, ex, code):
        raise ex

    def on_error(self, ex):
        raise ex

    @contextmanager
    def catch_errors(self):
        try:
            yield
        except BaseException as ex:
            if isinstance(ex, FetchException):
                self.on_fetch_failed(ex, ex.http_error.code)
            self.on_error(ex)

    async def run(self):
        with self.catch_errors():
            return await super().co()

    # rerun_cause: str = None

    # def co(self):
    #     return self.run_and_handle()

    # def needs_rerun(self, cause: str):
    #     self.rerun_cause = cause

    # async def run_and_handle(self):
    #     run = super().co()
    #     with self.catch_errors():
    #         result = await run
    #     while self.rerun_cause:
    #         rerun_cause = self.rerun_cause
    #         self.rerun_cause = None
    #         with self.catch_errors():
    #             result = await self.rerun(rerun_cause)
    #     return result


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
        return data['token'], data['expires_on']

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

    async def get_from_db(self):
        async with db.connect() as conn:
            qu = (
                'select token, expires_on from veil_creds where username = $1 and controller_ip = $2',
                self.username, self.controller_ip
            )
            data = await conn.fetch(*qu)
        if data:
            [[token, expires_on]] = data
            return token, expires_on
        return None, None

    def get_expiration_time(self, expires_on: str):
        # set it to be 2/3 of the original one
        end = parse_dt(expires_on)
        now = datetime.now(timezone.utc)
        delta = (end - now) * 2 / 3
        return now + delta


    async def run(self):
        token, expires_on = await self.get_from_db()
        if token:
            expired = datetime.now(timezone.utc) > expires_on
            if not expired:
                return token
        async with lock.token:
            # have to check the db for the token again:
            # maybe it has been fetched while we've been waiting to aquire the lock
            token, expires_on = await self.get_from_db()
            if token:
                expired = datetime.now(timezone.utc) > expires_on
                if not expired:
                    return token
                token, expires_on = await RefreshToken(controller_ip=self.controller_ip, token=token)
            else:
                token, expires_on = await FetchToken(controller_ip=self.controller_ip)
            expires_on = self.get_expiration_time(expires_on)
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

    @cached
    def url(self):
        return f"http://{self.controller_ip}/api/controllers/system-time"

    def on_fetch_failed(self, ex, code):
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