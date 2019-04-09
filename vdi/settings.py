
from . import SettingsDict

class Settings(SettingsDict):
    debug = True
    controller_ip = '192.168.20.120'

    pool = {
        'initial_size': 2,
        'reserve_size': 2,
    }


settings = Settings()