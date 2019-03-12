
from starlette.applications import Starlette

class SettingsDict(dict):

    def __init__(self):
        cls = self.__class__
        super().__init__(**{
            k: v for k, v in cls.__dict__.items()
            if not k.startswith('__')
        })

from .settings import settings

app = Starlette(debug=settings.get('debug'))


