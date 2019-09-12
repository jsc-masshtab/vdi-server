#from __future__ import annotations
#from dataclasses import dataclass
from typing import List

from classy_async.classy_async import Task

import jwt
from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, BaseUser, AuthCredentials
)
from db.db import db

from vdi.settings import settings

config = settings['jwt']


claim_label = {"iss": "issuer", "iat": "iat", "nbf": "nbf", "aud": "audience"}

# DEPRECATED
# class JWTUser(BaseUser):
#     def __init__(self, username: str, token: str, payload: dict) -> None:
#         self.username = username
#         self.token = token
#         self.payload = payload
#
#     @property
#     def is_authenticated(self) -> bool:
#         return True
#
#     @property
#     def display_name(self) -> str:
#         return self.username


#@dataclass()
class VDIUser:
    username = ""
    email = ""
    roles = () # List[str] = ()
    jwt_payload = None  # dict = None

    def __init__(self, username: str, email: str, roles:List[str] = (), jwt_payload: dict() = None):
        self.username = username
        self.email = email
        self.roles = roles
        self.jwt_payload = jwt_payload
        pass


    @classmethod
    def set(cls, user): # cls, user: VDIUser
        task = GetVDIUser()
        task.return_value = user
        return task

    @classmethod
    def get(cls):
        return GetVDIUser()


class GetVDIUser(Task):
    return_value = None

    def __init__(self, return_value: VDIUser):
        self.return_value = return_value

    async def run(self):
        return self.return_value


class JWTAuthenticationBackend(AuthenticationBackend):

    def __init__(self, prefix: str = 'jwt', username_field: str = 'username'):
        self.prefix = prefix
        self.username_field = username_field

    @classmethod
    def get_token_from_header(cls, authorization: str, prefix: str):
        """
        Parses the Authorization header and returns only the token

        :param authorization:
        :return:
        """
        try:
            scheme, token = authorization.split()
        except ValueError:
            raise AuthenticationError('Could not separate Authorization scheme and token')
        if scheme.lower() != prefix.lower():
            raise AuthenticationError('Authorization scheme {} is not supported'.format(scheme))
        return token

    def _decode(self, token, verify=True):
        """
        Take a JWT and return a decoded payload. Optionally, will verify
        the claims on the token.
        """
        secret = config['secret']
        algorithm = config['algorithm']
        kwargs = {}

        # for claim in config['claims']:
        #     if claim != "exp":
        #         setting = "claim_{}".format(claim.lower())
        #         if setting in self.config:  # noqa
        #             value = self.config.get(setting)
        #             kwargs.update({claim_label[claim]: value})

        kwargs["leeway"] = int(config['leeway'])
        if "claim_aud" in config:  # noqa
            kwargs["audience"] = config['claim_aud']
        if "claim_iss" in config:  # noqa
            kwargs["issuer"] = config['claim_iss']

        decoded = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            verify=verify,
            options={"verify_exp": config['verify_exp']},
            **kwargs
        )
        return decoded

    async def fetch_user(self, username):
        async with db.connect() as conn:
            qu = 'select email, m2m.role ' \
                 'from public.user as u left join user_role_m2m as m2m on u.username = m2m.username ' \
                 'where u.username = $1', username
            data = await conn.fetch(*qu)
        user = {'username': username}
        for [email, role] in data:
            user.setdefault('roles', []).append(role)
            user['email'] = email
        return user

    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        token = self.get_token_from_header(authorization=auth, prefix=self.prefix)
        try:
            payload = self._decode(token)
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(str(e))

        username = payload[self.username_field]
        user = await self.fetch_user(username)
        del payload[self.username_field]
        user = VDIUser(**user, jwt_payload=payload)
        return AuthCredentials(["authenticated"]), user
