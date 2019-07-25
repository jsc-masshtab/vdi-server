
from cached_property import cached_property as cached


class BackendError(Exception):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def format_error(self):
        return {
            **self.__dict__,
            'type': self.__class__.__name__
        }


class ApiError(BackendError):
    def __init__(self, data):
        self.data = data

    def format_error(self):
        return {
            'type': self.__class__.__name__,
            'data': self.data
        }


class FieldError(ApiError):
    def __init__(self, **kwargs):
        super().__init__(kwargs)


class SimpleError(ApiError):
    pass


class NotFound(Exception):
    pass


class FetchException(BackendError):
    def format_error(self):
        return {
            'type': self.__class__.__name__,
            'url': self.url,
            'message': self.message,
        }

class WsTimeout(BackendError):
    pass