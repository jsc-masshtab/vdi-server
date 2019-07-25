
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



class FetchException(BackendError):
    http_error: HTTPClientError
    url: str
    data: dict

    def format_error(self):
        return {
            'code': self.http_error.code,
            **self.data, **self.type_info
        }


class NotFound(BackendError):
    pass


class BadRequest(BackendError):
    errors: List

    def __init__(self, errors):
        self.errors = errors

    @classmethod
    def fetch_failed(cls, fetch_exc):
        return cls(errors=fetch_exc.data['errors'])

    def format_error(self):
        return {
            'code': 400, **self.type_info, **self.errors
        }


class NotFound(BackendError):
    def __init__(self, message):
        self.message = message

    def format_error(self):
        return {
            'code': self.code,
            'message': self.message,
        }


class WsTimeout(BackendError):
    pass