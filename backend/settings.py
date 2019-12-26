# -*- coding: utf-8 -*-
"""Project settings."""
# TODO: секретные штуки перенести в переменные окружения или более модные способы.


# Database settings
# -----------------------------

DB_HOST = 'localhost'
DB_PORT = 5432
DB_USER = 'postgres'
DB_PASS = 'postgres'
DB_NAME = 'vdi'

# Crypto settings
# -----------------------------
SECRET_KEY = 'RSrf948GB2YXQKBjXhikwxDDJbfooHoBuewQYqO1A2MyBqK15G'
FERNET_KEY = b'LRzSxWyxqKD4p2BR11-nVmghV67AVmQ4CxYi__S_OH8='

# JWT Options
# -----------------------------
JWT_EXPIRATION_DELTA = 86400
# JWT_EXPIRATION_DELTA = 60
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

# Pool parameters
# -----------------------------
# MIX_POOL_SIZE = 1
# MAX_POOL_SIZE = 200
# MAX_VM_AMOUNT_IN_POOL = 1000

# Others
# -----------------------------
DEFAULT_NAME = '-'

# Settings for tests
# -----------------------------
TESTS_ADMIN_USERNAME = 'admin'
TESTS_ADMIN_PASSWORD = 'qwe'
TESTS_LDAP_USERNAME = 'ad120'
TESTS_LDAP_PASSWORD = 'Bazalt1!'
TESTS_AD_DOMAIN_NAME = 'bazalt.team'
TESTS_AD_VERBOSE_NAME = 'Bazalt'
TESTS_AD_DIRECTORY_URL = 'ldap://192.168.11.180'