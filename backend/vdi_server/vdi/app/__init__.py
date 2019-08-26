
from .vars import Request


def __getattr__(name):
    if name == 'app':
        from vdi.app import base
        return base.app
    raise AttributeError