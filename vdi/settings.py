
from . import SettingsDict

class Settings(SettingsDict):
    debug = True
    controller_url = '192.168.20.120'


settings = Settings()