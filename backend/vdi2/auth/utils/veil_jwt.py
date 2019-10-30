# -*- coding: utf-8 -*-
"""JWT additions for Tornado"""
import jwt
import datetime
from settings import JWT_OPTIONS, SECRET_KEY, JWT_EXPIRATION_DELTA, JWT_AUTH_HEADER_PREFIX, JWT_ALGORITHM


def jwtauth(handler_class):
    """ Handle Tornado JWT Auth """

    def wrap_execute(handler_execute):
        def require_auth(handler, kwargs):
            try:
                token = extract_access_token(handler.request.headers)
                decode_jwt(token)
            except jwt.ExpiredSignature:
                handler._transforms = []
                handler.set_status(401)
                handler.finish('Token has expired.')
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


def encode_jwt(username):
    """Get JWT encoded token"""
    current_time = datetime.datetime.utcnow()
    expires_on = current_time + datetime.timedelta(seconds=JWT_EXPIRATION_DELTA)
    access_token_payload = {'exp': expires_on,
                            'username': username,
                            'iat': current_time.timestamp(),
                            }
    access_token = jwt.encode(
        payload=access_token_payload,
        key=SECRET_KEY,
        algorithm=JWT_ALGORITHM
    ).decode('utf-8')
    return {'access_token': access_token, 'expires_on': expires_on.strftime("%d.%m.%Y %H:%M:%S UTC")}


def decode_jwt(token, decode_options: dict = JWT_OPTIONS):
    """Decode JWT token"""
    try:
        decoded_jwt = jwt.decode(
            token,
            SECRET_KEY,
            options=decode_options
        )
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError()
    except Exception as E:  # noqa
        raise AssertionError("Error with JWT decode")
    return decoded_jwt


def extract_access_token(headers: dict) -> str:
    """Exctract JWT token from headers"""
    auth = headers.get('Authorization')
    if auth:
        parts = auth.split()
        if parts[0].upper() != JWT_AUTH_HEADER_PREFIX:
            raise AssertionError("invalid header authorization")
        elif len(parts) == 1:
            raise AssertionError("invalid header authorization")
        elif len(parts) > 2:
            raise AssertionError("invalid header authorization")
        access_token = parts[1]
        return access_token
    else:
        raise AssertionError("Missing Authorization header")


def extract_user(headers: dict) -> str:
    """Exctract user from token if token is valid"""
    token = extract_access_token(headers)
    decoded = decode_jwt(token)
    return decoded.get('username')


def refresh_access_token_with_no_expire_check(headers: dict):
    """Не проверяем срок действия токена при decode, но сличаем полученный токен с последним сохраненным."""
    access_token = extract_access_token(headers)
    JWT_OPTIONS['verify_exp'] = False
    payload = decode_jwt(access_token, JWT_OPTIONS)
    username = payload['username']
    # TODO: нужно взять пользователя из payload и iot и сравнить в таблице в БД. Дата должна совпадать
    return encode_jwt(username)


def refresh_access_token_with_expire_check(headers: dict):
    """Проверяем срок действия токена при decode. Если он действует - выдаем новый, если нет - ошибка."""
    access_token = extract_access_token(headers)
    payload = decode_jwt(access_token)
    username = payload['username']
    return encode_jwt(username)

