# -*- coding: utf-8 -*-
"""JWT additions for Tornado"""
import jwt
import datetime
from settings import JWT_OPTIONS, SECRET_KEY, JWT_EXPIRATION_DELTA


# TODO: refresh token

def jwtauth(handler_class):
    """ Handle Tornado JWT Auth """

    def wrap_execute(handler_execute):
        def require_auth(handler, kwargs):
            try:
                token = extract_token(handler.request.headers)
                decode_jwt(token)
            except AssertionError as e:
                handler._transforms = []
                handler.set_status(401)
                handler.finish(str(e))
            return True

        def _execute(self, transforms, *args, **kwargs):
            try:
                require_auth(self, kwargs)
            except:  # noqa
                return False
            return handler_execute(self, transforms, *args, **kwargs)
        return _execute
    handler_class._execute = wrap_execute(handler_class._execute)  # noqa
    return handler_class


def get_jwt(username):
    """Get JWT encoded token"""
    token = jwt.encode(
        payload={'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION_DELTA),
                 'username': username,
                 'time': str(datetime.datetime.utcnow()),
                 },
        key=SECRET_KEY,
        algorithm='HS256'
    )
    return {'access_token': token.decode('utf-8')}


def decode_jwt(token):
    """Decode JWT token"""
    try:
        decoded_jwt = jwt.decode(
            token,
            SECRET_KEY,
            options=JWT_OPTIONS
        )
    except:  # noqa
        raise AssertionError("Error with JWT decode")
    return decoded_jwt


def extract_token(headers: dict) -> str:
    """Exctract JWT token from headers"""
    auth = headers.get('Authorization')
    if auth:
        parts = auth.split()
        if parts[0].lower() != 'jwt':
            raise AssertionError("invalid header authorization")
        elif len(parts) == 1:
            raise AssertionError("invalid header authorization")
        elif len(parts) > 2:
            raise AssertionError("invalid header authorization")
        token = parts[1]
        return token
    else:
        raise AssertionError("Missing Authorization header")


def extract_user(headers: dict) -> str:
    """Exctract user from token if token is valid"""
    token = extract_token(headers)
    decoded = decode_jwt(token)
    return decoded.get('username')
