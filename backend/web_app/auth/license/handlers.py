# -*- coding: utf-8 -*-
from common.languages import _local_
from common.models.active_tk_connection import ActiveTkConnection
from common.models.license import License
from common.utils import gino_model_to_json_serializable_dict
from common.veil.auth.veil_jwt import jwtauth
from common.veil.veil_decorators import is_administrator
from common.veil.veil_errors import Unauthorized, ValidationError
from common.veil.veil_handlers import BaseHttpHandler


@jwtauth
class LicenseHandler(BaseHttpHandler):
    async def get(self):
        """Get license key info."""
        license_obj = await License.get_license()
        license_data = gino_model_to_json_serializable_dict(license_obj)

        response = await LicenseHandler._form_response(license_data, license_obj)
        return self.finish(response)

    async def post(self):
        """Upload license key."""
        # проверка наличия роли
        try:
            user = await self.get_user_object()
            roles = await user.roles
            if not is_administrator(roles):
                raise Unauthorized
        except (Unauthorized, AttributeError, TypeError):
            response = {"errors": [{"message": _local_("Invalid permissions.")}]}
            return await self.log_finish(response)
        # загрузка самого файла
        try:
            key_file_dict = dict()
            for file_name in self.request.files:
                if file_name.endswith(".key"):
                    key_file_dict = self.request.files.get(file_name)[0]
                    break

            if not key_file_dict:
                raise AssertionError("Can't extract file.")

            key_file_name = key_file_dict["filename"]
            if not key_file_name.endswith(".key"):
                raise ValidationError(_local_("Bad extension."))
            # TODO: check content_type of file - application/x-iwork-keynote-sffkey
            # key_file_content_type = key_file_dict.get('content_type')  # noqa

            key_file_body = key_file_dict.get("body")
            license_obj = await License.upload_license(key_file_body, user.username)
        except (IndexError, ValidationError, TypeError, AssertionError):

            response = {
                "errors": [
                    {
                        "message": _local_("Fail to open license key file.").format(
                            ip=self.remote_ip
                        )
                    }
                ]
            }
            return await self.log_finish(response)

        # Send response with license data
        license_data = gino_model_to_json_serializable_dict(license_obj)

        response = await LicenseHandler._form_response(license_data, license_obj)
        return await self.log_finish(response)

    @staticmethod
    async def _form_response(license_data, license_obj):
        thin_clients_conn_count = await ActiveTkConnection.get_thin_clients_conn_count()
        license_data["thin_clients_limit"] = license_obj.real_thin_clients_limit
        license_data["expired"] = license_obj.expired
        license_data["support_expired"] = license_obj.support_expired
        license_data["remaining_days"] = license_obj.remaining_days
        license_data["support_remaining_days"] = license_obj.support_remaining_days

        license_data["thin_clients_count"] = str(thin_clients_conn_count)
        response = {"data": license_data}
        return response
