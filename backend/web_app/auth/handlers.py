# -*- coding: utf-8 -*-
from abc import ABC

from common.languages import _local_
from common.log.journal import system_logger
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from common.models.authentication_directory import AuthenticationDirectory
from common.settings import EXTERNAL_AUTH, LOCAL_AUTH, PAM_AUTH
from common.veil.auth.veil_jwt import (
    encode_jwt,
    extract_user_and_token_with_no_expire_check,
)
from common.veil.veil_errors import AssertError, SilentError, ValidationError
from common.veil.veil_gino import EntityType
from common.veil.veil_handlers import BaseHttpHandler


class AuthHandler(BaseHttpHandler, ABC):
    async def post(self):
        try:
            if not self.args:
                raise ValidationError(_local_("Missing request body."))
            if "username" and "password" not in self.args:
                raise AssertError(_local_("Missing username and password."))

            username = self.args["username"]
            password = self.args["password"]
            if "code" in self.args:
                two_factor_code = self.args["code"]
            else:
                two_factor_code = None

            if not username or len(username) < 2:
                raise ValidationError(_local_("Missing username."))
            if not password or len(password) < 2:
                raise ValidationError(_local_("Missing password."))

            # Updated 26.12.2020
            if self.args.get("ldap") and EXTERNAL_AUTH:
                account_name = await AuthenticationDirectory.authenticate(
                    username, password
                )
                domain_name = await AuthenticationDirectory.get_domain_name(
                    self.args["username"]
                )
            elif self.args.get("ldap") and not EXTERNAL_AUTH:
                raise ValidationError(
                    _local_("External auth system is disabled. Check broker settings.")
                )
            elif PAM_AUTH and LOCAL_AUTH:
                raise ValidationError(
                    _local_("PAM or LOCAL auth only. Check broker settings.")
                )
            elif LOCAL_AUTH or PAM_AUTH:
                password_is_valid = await User.check_user(username, password)
                account_name = username
                domain_name = None
                if not password_is_valid:
                    raise AssertError(_local_("Invalid credentials."))
            else:
                raise ValidationError(
                    _local_("Auth system is disabled. Check broker settings.")
                )

            await User.check_2fa(username, two_factor_code)

            access_token = encode_jwt(account_name, domain=domain_name)

            if self.client_type == "thin-client":
                thin_client_limit_exceeded = await ActiveTkConnection.thin_client_limit_exceeded()
                if thin_client_limit_exceeded:
                    raise RuntimeError(_local_("Thin client limit exceeded."))

            await User.login(
                username=account_name,
                token=access_token.get("access_token"),
                ip=self.remote_ip,
                ldap=self.args.get("ldap"),
                client_type=self.client_type,
            )
            response = {"data": access_token}

        except RuntimeError as auth_error:
            await self._create_error_msg_and_log(auth_error)
            response = {"errors": [{"message": str(auth_error)}]}
            self.set_status(403)
        except AssertionError as auth_error:
            error_message = await self._create_error_msg_and_log(auth_error)
            response = {"errors": [{"message": error_message}]}
            self.set_status(200)
        except SilentError as auth_error:
            error_description = "IP: {}\n{}".format(self.remote_ip, str(auth_error))
            entity = {"entity_type": EntityType.SECURITY, "entity_uuid": None}
            await system_logger.warning(
                message=_local_("Authentication failed for user: {}.").format(self.args.get("username", "unknown")),
                entity=entity, description=error_description
            )
            response = {"errors": [{"message": str(auth_error)}]}
            self.set_status(200)
        return await self.log_finish(response)

    async def _create_error_msg_and_log(self, auth_error):
        error_description = "IP: {}\n{}".format(self.remote_ip, str(auth_error))
        entity = {"entity_type": EntityType.SECURITY, "entity_uuid": None}
        error_message = _local_("Authentication failed for user: {}.").format(
            self.args.get("username", "unknown")
        )
        await system_logger.warning(
            message=error_message, entity=entity, description=error_description
        )

        return error_message


class LogoutHandler(BaseHttpHandler, ABC):
    async def post(self):
        username, token = extract_user_and_token_with_no_expire_check(
            self.request.headers
        )
        await User.logout(username=username, access_token=token)
        await system_logger.debug(_local_("User {} logged out.").format(username))


class VersionHandler(BaseHttpHandler, ABC):
    async def get(self):
        info_dict = {
            "version": "3.1.2",
            "year": "2019-2021",
            "url": "https://mashtab.org",
            "copyright": "© mashtab.org",
        }
        response = {"data": info_dict}
        return self.finish(response)
