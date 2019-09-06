import asyncio


class SettingsDict(dict):

    def __init__(self):
        cls = self.__class__
        super().__init__(**{
            k: v for k, v in cls.__dict__.items()
            if not k.startswith('__')
        })
        self.__dict__ = self           # to allow dot access
        self.__class__ = SettingsDict  # to remove class attributes


from .settings import settings

from classy_async.classy_async import g
g.use_threadlocal(True) # Will be set to False when server starts

from vdi.application.app import app
