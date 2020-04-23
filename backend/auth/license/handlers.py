# -*- coding: utf-8 -*-
from abc import ABC

from common.veil_handlers import BaseHandler
from common.veil_errors import ValidationError
from auth.utils.veil_jwt import jwtauth
from auth.license.utils import License
from languages import lang_init


_ = lang_init()


@jwtauth
class LicenseHandler(BaseHandler, ABC):

    async def get(self):
        """get license key info"""

        license_data = License().license_data.public_attrs_dict
        response = {'data': license_data}
        return self.finish(response)

    async def post(self):
        """Upload license key"""

        try:
            key_file_dict = dict()
            for file_name in self.request.files:
                if file_name.endswith('.key'):
                    key_file_dict = self.request.files.get(file_name)[0]
                    break

            if not key_file_dict:
                raise AssertionError('Can\'t extract file.')

            key_file_name = key_file_dict['filename']
            if not key_file_name.endswith('.key'):
                raise ValidationError(_('Bad extension.'))

            # TODO: check content_type of file - application/x-iwork-keynote-sffkey
            # key_file_content_type = key_file_dict.get('content_type')  # noqa

            key_file_body = key_file_dict.get('body')
            response = License().upload_license(key_file_body)
        except (IndexError, ValidationError, TypeError, AssertionError):
            response = {'errors': [{'message': _('Fail to open license key file.').format(ip=self.remote_ip)}]}
        return self.log_finish(response)
