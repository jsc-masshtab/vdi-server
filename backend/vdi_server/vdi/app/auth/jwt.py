import jwt
from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, BaseUser, AuthCredentials
)

from vdi.settings import settings

config = settings['jwt']


claim_label = {"iss": "issuer", "iat": "iat", "nbf": "nbf", "aud": "audience"}

class JWTUser(BaseUser):
    def __init__(self, username: str, token: str, payload: dict) -> None:
        self.username = username
        self.token = token
        self.payload = payload

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.username


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
            raise AuthenticationError(f'Authorization scheme {scheme} is not supported')
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


    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        token = self.get_token_from_header(authorization=auth, prefix=self.prefix)
        try:
            payload = self._decode(token)
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(str(e))

        return AuthCredentials(["authenticated"]), JWTUser(username=payload[self.username_field], token=token,
                                                           payload=payload)
