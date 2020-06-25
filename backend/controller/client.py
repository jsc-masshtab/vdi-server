# -*- coding: utf-8 -*-
from datetime import datetime

from common.veil_client import VeilHttpClient

from languages import lang_init
from common.veil_errors import ValidationError

_ = lang_init()


class ControllerClient(VeilHttpClient):

    def __init__(self, controller_ip: str):
        super().__init__(controller_ip)

    async def auth(self, auth_info):
        """Авторизация на контроллере и получение токена."""
        method = 'POST'
        headers = {'Content-Type': 'application/json',
                   'User-Agent': 'VeiL-api-client/1.0 VDI/2.0',
                   'Accept-Language': 'en',
                   'Cache-Control': 'max-age=0',
                   'Accept-Charset': 'utf-8',
                   'Connection': 'close'
                   }
        url = 'http://{}/auth/'.format(self.controller_ip)
        response = await self.fetch_with_response(url=url, method=method, headers=headers, body=auth_info)
        token = response.get('token')
        expires_on = datetime.strptime(response.get('expires_on'), "%d.%m.%Y %H:%M:%S UTC")
        if not token or not expires_on:
            raise ValidationError(_('Auth failed.'))
        self.token = token
        return token, expires_on

    async def fetch_version(self):
        """Получить версию контроллера."""
        url = self.api_url + 'controllers/base-version/'
        response = await self.fetch_with_response(url=url, method='GET')
        return response.get('version')
