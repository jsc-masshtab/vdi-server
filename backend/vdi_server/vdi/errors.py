
from cached_property import cached_property as cached

class ApiError(Exception):

    def __init__(self, data):
        self.data = data

    @cached
    def type(self):
        return self.__class__.__name__

    def format_error(self):
        return {
            "type": self.type,
            "data": self.data
        }


class FieldError(ApiError):

    def __init__(self, **kwargs):
        super().__init__(kwargs)


class SimpleError(ApiError):
    pass


class HttpError(Exception):
    pass


class NotFound(HttpError):
    pass