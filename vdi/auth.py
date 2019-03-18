

from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, SimpleUser, UnauthenticatedUser,
    AuthCredentials
)
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware


from asyncpg.connection import Connection

from . import app
from .db import db

class SessionAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        username = request.session.get('username')
        if username:
            return AuthCredentials(["authenticated"]), SimpleUser(username)



app.add_middleware(AuthenticationMiddleware, backend=SessionAuthBackend())
app.add_middleware(SessionMiddleware, secret_key='sphere')


