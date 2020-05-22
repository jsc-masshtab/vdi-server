# -*- coding: utf-8 -*-
from abc import ABC

from common.veil_handlers import BaseHandler
from database import EntityType
from auth.utils.veil_jwt import encode_jwt, extract_user_and_token_with_no_expire_check
from auth.models import User
from auth.authentication_directory.models import AuthenticationDirectory

from languages import lang_init
from journal.journal import Log as log
from common.veil_errors import ValidationError, AssertError


_ = lang_init()


class AuthHandler(BaseHandler, ABC):

    async def post(self):
        try:
            if not self.args:
                raise ValidationError(_('Missing request body'))
            if 'username' and 'password' not in self.args:
                raise AssertError(_('Missing username and password'))

            username = self.args['username']
            password = self.args['password']
            if not username or len(username) < 2:
                raise ValidationError(_('Missing username'))
            if not password or len(password) < 2:
                raise ValidationError(_('Missing password'))

            if self.args.get('ldap'):
                account_name = await AuthenticationDirectory.authenticate(username, password)
                domain_name = await AuthenticationDirectory.get_domain_name(self.args['username'])
            else:
                password_is_valid = await User.check_user(username, password)
                account_name = username
                domain_name = None
                if not password_is_valid:
                    raise AssertError(_('Invalid credentials'))

            access_token = encode_jwt(account_name, domain=domain_name)
            await User.login(username=account_name, token=access_token.get('access_token'), ip=self.remote_ip,
                             ldap=self.args.get('ldap'), client_type=self.client_type)
            response = {'data': access_token}
        except AssertionError as auth_error:
            error_message = _('Authentication failed: {err}').format(err=auth_error)
            if self.args.get('username'):
                error_message += _(' for user {username}').format(username=self.args['username'])
            error_message += _('. IP: {ip}').format(ip=self.remote_ip)
            entity = {'entity_type': EntityType.SECURITY, 'entity_uuid': None}
            await log.warning(error_message, entity_dict=entity)
            response = {'errors': [{'message': error_message}]}
            self.set_status(200)
        return self.log_finish(response)


class LogoutHandler(BaseHandler, ABC):
    async def post(self):
        username, token = extract_user_and_token_with_no_expire_check(self.request.headers)
        await User.logout(username=username, access_token=token)
        log.debug(_('User {} logout with token {}').format(username, token))


class VersionHandler(BaseHandler, ABC):
    async def get(self):
        response = {'data': {'version': '2.0.1',
                             'year': '2019-2020',
                             'url': 'https://mashtab.org',
                             'copyright': '©mashtab.org',
                             'comment': _('Demo version')}}
        return self.finish(response)
