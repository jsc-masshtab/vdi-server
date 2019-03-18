
from . import SettingsDict

class Settings(SettingsDict):
    debug = True
    controller_ip = '192.168.20.120'


settings = Settings()