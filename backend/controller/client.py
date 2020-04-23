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
        headers = {'Content-Type': 'application/json'}
        url = 'http://{}/auth/'.format(self.controller_ip)
        response = await self.fetch_with_response(url=url, method=method, headers=headers, body=auth_info)
        self.token = response.get('token')
        self.expires_on = datetime.strptime(response.get('expires_on'), "%d.%m.%Y %H:%M:%S UTC")
        if not self.token or not self.expires_on:
            raise ValidationError(_('Auth failed.'))
        return self.token, self.expires_on

    async def fetch_version(self):
        """check if controller accesseble"""
        url = self.api_url + 'controllers/base-version/'
        response = await self.fetch_with_response(url=url, method='GET')
        return response.get('version')
