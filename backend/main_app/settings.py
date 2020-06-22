# -*- coding: utf-8 -*-
"""Project settings."""
import os

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
VEIL_MAX_BODY_SIZE = 1000 * 1024 ^ 3
VEIL_MAX_CLIENTS = 10
VEIL_SSL_ON = False
VEIL_WS_MAX_TIME_TO_WAIT = 60

# Locale settings
# -----------------------------
LANGUAGE = 'ru'

# Others
# -----------------------------
DEFAULT_NAME = '-'
LDAP_TIMEOUT = 5

# File system paths
# -----------------------------
SERIAL_KEY_FNAME = 'serial.key'
PRIVATE_PEM_FNAME = 'veil_vdi.pem'
SERIAL_KEY_FPATH = os.path.join('../', SERIAL_KEY_FNAME)
PRIVATE_PEM_FPATH = os.path.join('auth/license', PRIVATE_PEM_FNAME)

# Redis settings
# -----------------------------
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = '4NZ7GpHn4IlshPhb'
REDIS_TIMEOUT = 5
REDIS_THIN_CLIENT_CHANNEL = 'TC_CHANNEL'

try:
    from local_settings import *  # noqa
except ImportError:
    pass

REDIS_URL = 'redis://:{}@localhost:{}/{}'.format(REDIS_PASSWORD, REDIS_PORT, REDIS_DB)