# -*- coding: utf-8 -*-
from abc import ABC

from common.veil_handlers import BaseHandler
from auth.utils.veil_jwt import jwtauth
from auth.license.utils import License

# TODO: мультиязычность


@jwtauth
class LicenseHandler(BaseHandler, ABC):

    async def get(self):
        """get license key info"""

        license_data = License().get_license()
        response = {'data': license_data}
        return self.finish(response)

    async def post(self):
        """Upload license key"""

        try:
            key_file_dict = self.request.files.get('keyFile')[0]

            key_file_name = key_file_dict['filename']
            if not key_file_name.endswith('.key'):
                raise AssertionError('Bad extension.')

            key_file_content_type = key_file_dict.get('content_type')  # noqa
            # TODO: check content_type of file - application/x-iwork-keynote-sffkey

            key_file_body = key_file_dict.get('body')
            response = License().upload_license(key_file_body)
        except (IndexError, AssertionError, TypeError):
            response = {'errors': [{'message': 'Проблема обработки ключа.'}]}
        return self.finish(response)
