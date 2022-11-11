# -*- coding: utf-8 -*-
from packaging import version

from tornado.web import HTTPError

from common import settings
from common.languages import _local_
from common.log.journal import system_logger
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from common.models.authentication_directory import AuthenticationDirectory
from common.veil.auth.auth_dir_utils import extract_domain_from_username
from common.veil.auth.veil_jwt import (
    encode_jwt,
    extract_user_and_token_with_no_expire_check,
)
from common.veil.veil_errors import AssertError, MeaningError, SilentError, ValidationError
from common.veil.veil_gino import EntityType
from common.veil.veil_handlers import BaseHttpHandler


class AuthHandler(BaseHttpHandler):
    async def post(self):
        try:
            if not self.args:
                raise ValidationError(_local_("Missing request body."))
            if "username" and "password" not in self.args:
                raise AssertError(_local_("Missing username and password."))

            username = self.args["username"]
            password = self.args["password"]

            if not username or len(username) < 2:
                raise ValidationError(_local_("Missing username."))
            if not password or len(password) < 2:
                raise ValidationError(_local_("Missing password."))

            password_expired = await User.check_password_expiration(username)
            if password_expired:
                raise MeaningError(_local_("The password for user {} has expired.").format(username))

            # Updated 26.12.2020
            if self.args.get("ldap") and settings.EXTERNAL_AUTH:
                account_name = await AuthenticationDirectory.authenticate(username, password)
                domain_name = await AuthenticationDirectory.get_domain_name(self.args["username"])
            elif self.args.get("ldap") and not settings.EXTERNAL_AUTH:
                raise ValidationError(
                    _local_("External auth system is disabled. Check broker settings.")
                )
            elif settings.PAM_AUTH and settings.LOCAL_AUTH:
                raise ValidationError(
                    _local_("PAM or LOCAL auth only. Check broker settings.")
                )
            elif settings.LOCAL_AUTH or settings.PAM_AUTH:
                password_is_valid = await User.check_user(username, password)
                account_name = username
                domain_name = None
                if not password_is_valid:
                    raise AssertError(_local_("Invalid credentials."))
            else:
                raise ValidationError(
                    _local_("Auth system is disabled. Check broker settings.")
                )

            await User.check_2fa(username, self.args.get("code"))

            access_token = encode_jwt(account_name, domain=domain_name)
            if self.client_type == "thin-client":
                await self._validate_desktop_thin_client_version()
                await self._validate_thin_client_limit()

            await User.login(
                username=account_name,
                token=access_token.get("access_token"),
                ip=self.remote_ip,
                ldap=self.args.get("ldap"),
                client_type=self.client_type,
            )
            response = {"data": access_token}
        # TODO: Почему при неудаче код 200 в исключениях? Возвращать 403
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
        except MeaningError as auth_error:
            error_description = "IP: {}.".format(self.remote_ip)
            entity = {"entity_type": EntityType.SECURITY, "entity_uuid": None}
            await system_logger.warning(
                message=str(auth_error),
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

    async def _validate_desktop_thin_client_version(self):

        base_error_msg = f"Minimum supported desktop client version is" \
                         f" {settings.MINIMUM_SUPPORTED_DESKTOP_THIN_CLIENT_VERSION}"  # noqa

        if "veil_connect_version" not in self.args:
            raise RuntimeError(_local_(f"Missing VeiL Connect version. {base_error_msg}."))
        else:
            veil_connect_version = self.args["veil_connect_version"]
            min_supported_version = settings.MINIMUM_SUPPORTED_DESKTOP_THIN_CLIENT_VERSION
            if version.parse(veil_connect_version) < version.parse(min_supported_version):
                raise RuntimeError(
                    _local_(f"Version {veil_connect_version} is not supported. {base_error_msg}.")
                )

    async def _validate_thin_client_limit(self):
        thin_client_limit_exceeded = await ActiveTkConnection.thin_client_limit_exceeded()
        if thin_client_limit_exceeded:
            raise RuntimeError(_local_("Thin client limit exceeded."))


class LogoutHandler(BaseHttpHandler):
    async def post(self):
        username, token = extract_user_and_token_with_no_expire_check(
            self.request.headers
        )
        await User.logout(username=username, access_token=token)
        await system_logger.debug(_local_("User {} logged out.").format(username))


class VersionHandler(BaseHttpHandler):
    async def get(self):
        info_dict = {
            "version": "4.1.5",
            "year": "2019-2022",
            "url": settings.BROKER_URL,
            "copyright": settings.BROKER_COPYRIGHT,
        }
        response = {"data": info_dict}
        return self.finish(response)


class SettingsHandler(BaseHttpHandler):
    async def get(self):
        try:
            from common.broker_name import BROKER_NAME
        except ImportError:
            from common.settings import BROKER_NAME
        auth_dir = await AuthenticationDirectory.get_objects(first=True)
        data = {"language": settings.LANGUAGE,
                "broker_name": BROKER_NAME,
                "sso": auth_dir.sso if auth_dir else False,
                "ldap": auth_dir.dc_str if auth_dir else ""}
        response = {"data": data}
        return self.finish(response)


class KerberosAuthHandler(BaseHttpHandler):
    async def get(self):
        auth_dir = await AuthenticationDirectory.get_objects(first=True)
        if auth_dir and auth_dir.sso:
            auth_header = self.request.headers.get("Authorization")
            remote_user = self.request.headers.get("X-Remote-User")
            if auth_header and remote_user:
                await system_logger.debug("KerberosAuthHandler user: {}".format(remote_user))  # To see what you get
                account_name, domain_name = extract_domain_from_username(remote_user)
                access_token = encode_jwt(account_name, domain=domain_name)
                await User.login(
                    username=account_name,
                    token=access_token.get("access_token"),
                    ip=self.remote_ip,
                    ldap=True,
                    client_type=self.client_type,
                )
                response = {"data": access_token}
                return await self.log_finish(response)
            else:
                raise HTTPError(500, "Kerberos auth error")
        else:
            raise HTTPError(401, "Kerberos auth is unable")
