# -*- coding: utf-8 -*-
"""Old errors moved from Vdi v0.2"""
import asyncio

from abc import ABC

from common.languages import lang_init
from common.log.journal import system_logger


_ = lang_init()


class ValidationError(AssertionError):
    def __init__(self, message):
        system_logger._debug(message)


class InvalidUserError(ValidationError):
    def __init__(self, message):
        super().__init__(message)


class AssertError(AssertionError):
    def __init__(self, message):
        system_logger._debug(message)


class MeaningError(ValueError):
    def __init__(self, message):
        system_logger._debug(message)


class BackendError(Exception):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @property
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
    def __init__(self, message, **kwargs):
        native_loop = asyncio.get_event_loop()
        self.create_event = native_loop.create_task(self.create_error_event(message, **kwargs))
        self.message = message

    def format_error(self):
        return self.message

    @staticmethod
    async def create_error_event(message, **kwargs):
        await system_logger.error(message, **kwargs)


class SilentError(BackendError):
    def __init__(self, message=None):
        if message:
            message = str(message)
            system_logger._debug(message)
            self.message = message

    def format_error(self):
        return self.message


class FetchException(BackendError):
    http_error = None   # HTTPClientError
    url = ''
    data = dict()

    @property
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
            message = str(message)
            system_logger._debug(message)
            self.message = message

    @property
    def code(self):
        raise NotImplementedError

    def format_error(self):
        return {
            'type': 'HttpError', 'code': self.code, 'message': self.message,
        }


class NotFound(HttpError):
    def __init__(self, message, url):
        message = str(message)
        native_loop = asyncio.get_event_loop()
        self.create_event = native_loop.create_task(self.create_error_event(message))
        self.message = message
        self.url = url

    def code(self):
        return 404

    def format_error(self):
        return {
            **super().format_error(), **self.__dict__
        }

    @staticmethod
    async def create_error_event(message):
        await system_logger.error(message)


class BadRequest(HttpError):
    def __init__(self, errors):
        system_logger._debug('BadRequest: {}'.format(errors))
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


# class ControllerNotAccessible(HttpError):
#     code = 408
#     message = _('Controller is not available.')
#     system_logger._debug(message)
#
#     def __init__(self, *, ip):
#         self.ip = ip
#
#     def format_error(self):
#         return {
#             'ip': self.ip, **super().format_error()
#         }


class AuthError(HttpError, ABC):
    pass


class Forbidden(AuthError):
    code = 403
    message = _("Unable to logon to system using these credentials.")
    # TODO: раскомментируй меня (26.07.2020)
    # system_logger._debug(message)


class Unauthorized(AuthError):
    code = 401
    message = _('401: Unauthorized.')
    # TODO: раскомментируй меня (26.07.2020)
    # system_logger._debug(message)


class ServerError(HttpError):
    code = 500
    message = _("Critical controller error.")
    # TODO: раскомментируй меня (26.07.2020)
    # raise DeprecationWarning('will be deprecated in 2.1.0')
    # system_logger._debug(message)


class VmCreationError(Exception):
    def __init__(self, message):
        message = str(message)
        native_loop = asyncio.get_event_loop()
        self.create_event = native_loop.create_task(self.create_error_event(message))
        self.message = message

    @staticmethod
    async def create_error_event(message):
        await system_logger.error(message)


class PoolCreationError(Exception):
    def __init__(self, message):
        message = str(message)
        native_loop = asyncio.get_event_loop()
        self.create_event = native_loop.create_task(self.create_error_event(message))
        self.message = message

    @staticmethod
    async def create_error_event(message):
        await system_logger.error(message)
