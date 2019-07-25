

class BackendError(Exception):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def format_error(self):
        return {
            **self.__dict__,
            'type': self.__class__.__name__
        }



class FieldError(BackendError):
    def __init__(self, **kwargs):
        self.data = kwargs

    def format_error(self):
        return {
            'type': self.__class__.__name__,
            'data': self.data
        }


class SimpleError(BackendError):
    def __init__(self, message):
        self.message = message

    def format_error(self):
        return self.message



class FetchException(BackendError):
    def format_error(self):
        return {
            'type': self.__class__.__name__,
            'url': self.url,
            'message': self.message,
        }


class HttpError(BackendError):
    def __init__(self, code, message):
        self.message = message
        self.code = code

    def format_error(self):
        return {
            'code': self.code,
            'message': self.message,
        }


class WsTimeout(BackendError):
    pass