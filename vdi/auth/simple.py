

from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, SimpleUser, UnauthenticatedUser,
    AuthCredentials
)


class SessionAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        username = request.session.get('username')
        if username:
            return AuthCredentials(["authenticated"]), SimpleUser(username)


######

