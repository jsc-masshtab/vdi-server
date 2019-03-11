

from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, SimpleUser, UnauthenticatedUser,
    AuthCredentials
)
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware


from starlette.responses import PlainTextResponse
import base64
import binascii

from asyncpg.connection import Connection

from . import app
from .db import db

class BasicAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != 'basic':
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError('Invalid basic auth credentials')

        username, _, password = decoded.partition(":")
        # ignored for now
        user = self.get_user(username, password)
        if user:
            return AuthCredentials(["authenticated"]), SimpleUser(username)

    @db.connect()
    def get_user(self, username, password, conn: Connection):
        qu = '''
        SELECT 1 from public.user
        WHERE username = $1 AND password = $2
        ''', username, password
        res = await conn.fetch(*qu)
        if len(res) == 1:
            return {
                'username': username,
                'password': password,
            }


app.add_middleware(AuthenticationMiddleware, backend=BasicAuthBackend())

app.add_middleware(SessionMiddleware)