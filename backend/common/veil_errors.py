# -*- coding: utf-8 -*-
"""Old errors moved from Vdi v0.2"""
from abc import ABC

from cached_property import cached_property

from languages import lang_init


_ = lang_init()


class ValidationError(AssertionError):
    pass


class BackendError(Exception):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @cached_property
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
    http_error = None   # HTTPClientError
    url = ''
    data = dict()

    @cached_property
    def code(self):
        return self.http_error.code

    def format_error(self):
        return {
            'code': self.code,
            'url': self.url,
            **self.data,
            **self.type_info
        }

    def __repr__(self):
        return 'FetchException{}'.format(repr(self.__dict__))


class HttpError(BackendError):
    """
    Usually used to rethrow the FetchException to be consumed by the client
    """

    def __init__(self, message=None):
        if message:
            self.message = message

    @cached_property
    def code(self):
        raise NotImplementedError

    def format_error(self):
        return {
            'type': 'HttpError', 'code': self.code, 'message': self.message,
        }


class NotFound(HttpError):
    def __init__(self, message, url):
        self.message = message
        self.url = url

    def code(self):
        return 404

    def format_error(self):
        return {
            **super().format_error(), **self.__dict__
        }


class BadRequest(HttpError):

    def __init__(self, errors):
        self.errors = errors

    def code(self):
        return 400

    @classmethod
    def fetch_failed(cls, fetch_exc):
        return cls(errors=fetch_exc.data['errors'])

    def format_error(self):
        return {
            'type': 'HttpError', 'code': self.code, **self.errors
        }


class ControllerNotAccessible(HttpError):
    code = 408
    message = _('Controller is not available.')

    def __init__(self, *, ip):
        self.ip = ip

    def format_error(self):
        return {
            'ip': self.ip, **super().format_error()
        }


class AuthError(HttpError, ABC):
    pass


class Forbidden(AuthError):
    code = 403
    message = _("Unable to logon to system using these credentials.")


class Unauthorized(AuthError):
    code = 401


class ServerError(HttpError):
    code = 500
    message = _("Critical controller error.")


class VmCreationError(Exception):
    pass


class PoolCreationError(Exception):
    pass
