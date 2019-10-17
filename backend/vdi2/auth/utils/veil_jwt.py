# -*- coding: utf-8 -*-
"""JWT additions for Tornado"""
import jwt
import datetime
from settings import JWT_OPTIONS, SECRET_KEY, JWT_EXPIRATION_DELTA


def jwtauth(handler_class):
    """ Handle Tornado JWT Auth """

    def wrap_execute(handler_execute):
        def require_auth(handler, kwargs):
            auth = handler.request.headers.get('Authorization')
            if auth:
                parts = auth.split()
                if parts[0].lower() != 'jwt':
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()
                elif len(parts) == 1:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()
                elif len(parts) > 2:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()
                token = parts[1]
                try:
                    jwt.decode(
                        token,
                        SECRET_KEY,
                        options=JWT_OPTIONS
                    )
                except Exception as e:
                    handler._transforms = []
                    handler.set_status(401)
                    if hasattr(e, 'message'):
                        handler.write(e.message)
                    else:
                        handler.write(str(e))
                    handler.finish()
            else:
                handler._transforms = []
                handler.write("Missing authorization")
                handler.finish()
            return True

        def _execute(self, transforms, *args, **kwargs):
            try:
                require_auth(self, kwargs)
            except:  # noqa
                return False
            return handler_execute(self, transforms, *args, **kwargs)
        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
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
