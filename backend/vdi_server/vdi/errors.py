
from tornado.httpclient import HTTPClientError
from cached_property import cached_property as cached

from typing import List

class BackendError(Exception):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @cached
    def type_info(self):
        return {'type': self.__class__.__name__}

    def format_error(self):
        return {
            **self.__dict__, **self.type_info
        }



class FieldError(BackendError):
    def __init__(self, **kwargs):
        self.data = kwargs

    def format_error(self):
        return {
            'data': self.data, **self.type_info
        }


class SimpleError(BackendError):
    def __init__(self, message):
        self.message = message

    def format_error(self):
        return self.message



class WsTimeout(BackendError):
    pass


class FetchException(BackendError):
    http_error: HTTPClientError
    url: str
    data: dict

    @cached
    def code(self):
        return self.http_error.code

    def format_error(self):
        return {
            'code': self.code,
            'url': self.url,
            **self.data,
            **self.type_info
        }


class HttpError(BackendError):
    """
    Usually used to rethrow the FetchException to be consumed by the client
    """

    def __init__(self, message=None):
        if message:
            self.message = message

    @cached
    def code(self):
        raise NotImplementedError

    def format_error(self):
        return {
            'type': 'HttpError', 'code': self.code, 'message': self.message,
        }


class NotFound(HttpError):
    code = 404
    message = "Урл не найден"

    def __init__(self, *, text=None, url=None):
        if text:
            self.message = text
        if url:
            self.url = url

    def format_error(self):
        return {
            **super().format_error(), **self.__dict__
        }


class BadRequest(HttpError):
    code = 400
    errors: List

    def __init__(self, errors):
        self.errors = errors

    @classmethod
    def fetch_failed(cls, fetch_exc):
        return cls(errors=fetch_exc.data['errors'])

    def format_error(self):
        return {
            'type': 'HttpError', 'code': self.code, **self.errors
        }


class ControllerNotAccessible(HttpError):
    code = 404
    message = 'Контроллер недоступен'

    def __init__(self, *, ip):
        self.ip = ip

    def format_error(self):
        return {
            'ip': self.ip, **super().format_error()
        }


class AuthError(HttpError):
    code = 403
    message = "Не удалось войти в систему с предоставленными учетными данными."

