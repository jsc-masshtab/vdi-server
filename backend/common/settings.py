# -*- coding: utf-8 -*-
"""Project settings."""
import os

SETTINGS_PATH = os.path.dirname(__file__)

# Crypto settings
# -----------------------------

SECRET_KEY = 'RSrf948GB2YXQKBjXhikwxDDJbfooHoBuewQYqO1A2MyBqK15G'
FERNET_KEY = b'LRzSxWyxqKD4p2BR11-nVmghV67AVmQ4CxYi__S_OH8='

# Database settings
# -----------------------------

DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'vdi'
DB_USER = 'postgres'
DB_PASS = 'postgres'

# Pool settings
POOL_MIN_SIZE = 1
POOL_MAX_SIZE = 200
POOL_MAX_VM_AMOUNT = 1000
POOL_MAX_CREATE_ATTEMPTS = 15

# Journal settings
DEBUG = True

# Auth settings
# -----------------------------
# Включает/выключает проверку токенов, стандартный интерфейс GraphQL становится недоступным/доступным
AUTH_ENABLED = True

# JWT Options
# -----------------------------
JWT_EXPIRATION_DELTA = 86400
JWT_OPTIONS = {
    'verify_signature': True,
    'verify_exp': True,
    'verify_nbf': False,
    'verify_iat': True,
    'verify_aud': False
}
JWT_AUTH_HEADER_PREFIX = 'JWT'
JWT_ALGORITHM = 'HS256'

# Websocket settings
# -----------------------------
WS_PING_INTERVAL = 6
WS_PING_TIMEOUT = 300

# ECP Veil settings
# -----------------------------
VEIL_REQUEST_TIMEOUT = 15
VEIL_CONNECTION_TIMEOUT = 15
VEIL_OPERATION_WAITING = 10
VEIL_MAX_BODY_SIZE = 1000 * 1024 ^ 3
VEIL_MAX_CLIENTS = 10
VEIL_SSL_ON = False
VEIL_WS_MAX_TIME_TO_WAIT = 60
VEIL_CACHE_TTL = 1
VEIL_CACHE_TYPE = 'memcached'
VEIL_CACHE_SERVER = ('localhost', 11211)
VEIL_VM_PREPARE_TIMEOUT = 60 * 10

# Locale settings
# -----------------------------
LANGUAGE = 'ru'

# Partition settings
# -----------------------------
# PARTITION - Партиционирование и архивирование  по периоду: 0 - каждый день, 1 - каждую неделю, 2 - месяц, 3 - год
# BY_COUNT - Включение/отключение архивирования по количеству записей (при true партиционирование будет помесячно)
# COUNT - Количество записей, которые будут в архиве
# PATH - Путь до директории с архивами
# CREATE - Дата установки, для дальнейшего отсчета 3 лет хранения таблиц
PARTITION = 2
BY_COUNT = False
COUNT = 1000
PATH = '/tmp/'
CREATE = '2020-08-01'
# TODO: посмотреть скрипт archive_csv_journal
print(PATH)

# Others
# -----------------------------
DEFAULT_NAME = '-'
LDAP_TIMEOUT = 5

# File system paths
# -----------------------------
LOCALES_PATH = os.path.join(SETTINGS_PATH, 'locales/')
LICENSE_PATH = os.path.join(SETTINGS_PATH, '../web_app/auth/license/')
SERIAL_KEY_FNAME = 'serial.key'
PRIVATE_PEM_FNAME = 'veil_vdi.pem'
PRIVATE_PEM_FPATH = os.path.join(LICENSE_PATH, PRIVATE_PEM_FNAME)
SERIAL_KEY_FPATH = os.path.join(LICENSE_PATH, SERIAL_KEY_FNAME)

# Redis settings
# -----------------------------
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = '4NZ7GpHn4IlshPhb'
REDIS_TIMEOUT = 5
REDIS_THIN_CLIENT_CHANNEL = 'TC_CHANNEL'

try:
    from .local_settings import *  # noqa
except ImportError:
    pass

REDIS_URL = 'redis://:{}@localhost:{}/{}'.format(REDIS_PASSWORD, REDIS_PORT, REDIS_DB)
