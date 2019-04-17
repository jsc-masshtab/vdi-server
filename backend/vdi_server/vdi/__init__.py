
class SettingsDict(dict):

    def __init__(self):
        cls = self.__class__
        super().__init__(**{
            k: v for k, v in cls.__dict__.items()
            if not k.startswith('__')
        })

from .settings import settings

from classy_async import g
g.use_threadlocal(True) # Will be set to False when server starts

