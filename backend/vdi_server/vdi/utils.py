import inspect
from functools import wraps

from vdi.settings import settings

class Unset:
    pass


def print(msg, _print=print):
    if getattr(settings, 'print', False):
        _print(msg)