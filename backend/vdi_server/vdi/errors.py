
from cached_property import cached_property as cached


class BackendError(Exception):
    def format_error(self):
        return {
            'type': self.__class__.__name__
        }


class ApiError(BackendError):
    def __init__(self, data):
        self.data = data

    @cached
    def type(self):
        return self.__class__.__name__

    def format_error(self):
        type_info = super().format_error()
        return {
            **type_info, 'data': self.data
        }


class FieldError(ApiError):
    def __init__(self, **kwargs):
        super().__init__(kwargs)


class SimpleError(ApiError):
    pass


class NotFound(Exception):
    pass


class FetchException(BackendError):
    def __init__(self, msg, *, url, http_error):
        self.http_error = http_error
        self.url = url
        super().__init__(msg)

    def format_error(self):
        type_info = super().format_error()
        return {
            **type_info, 'url': self.url, 'message': str(self),
        }