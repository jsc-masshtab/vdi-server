
from . import SettingsDict

class Settings(SettingsDict):
    debug = True
    is_dev = True
    controller_ip = '192.168.20.120'


    pool = {
        'initial_size': 2,
        'reserve_size': 2,
    }

    jwt = {
        'algorithm': 'HS256',
        'secret': 'this_is_secret',
        'claims': ['exp'],
        'leeway': 180,
        'verify_exp': True,
    }

    credentials = {
        'username': 'vdi',
        'password': '4ever',
    }


settings = Settings()

try:
    from .local_settings import *
except ImportError:
    pass