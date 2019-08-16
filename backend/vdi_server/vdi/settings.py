
from . import SettingsDict

class Settings(SettingsDict):
    debug = True
    is_dev = True
    controller_ip = '192.168.20.120'
    print = False


    pool = {
        'initial_size': 2,
        'reserve_size': 2,
        'total_size': 2,
    }

    secret_key = 'this_is_secret'

    jwt = {
        'algorithm': 'HS256',
        'secret': secret_key,
        'claims': ['exp'],
        'leeway': 180,
        'verify_exp': True,
        'expiration_delta': 60 * 30,
    }

    credentials = {
        'username': 'vdi',
        'password': '4ever',
    }

    ws = {
        'timeout': 5 * 60
    }

    auth_server = {
        'port': 5000
    }


settings = Settings()

try:
    from .local_settings import settings as local_settings
except ImportError:
    pass

settings.update(local_settings)
