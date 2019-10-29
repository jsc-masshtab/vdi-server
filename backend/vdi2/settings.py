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

# Websocket settings
WS_PING_INTERVAL = 1  # TODO: изменить на 6, после доработки на стороне тонкого клиента.

# ECP Veil settings
# -----------------------------
VEIL_CREDENTIALS = dict(username='vdi', password='veil')  # TODO: remove
VEIL_REQUEST_TIMEOUT = 15
VEIL_CONNECTION_TIMEOUT = 15
VEIL_MAX_BODY_SIZE = 10 * 1024 ^ 3
VEIL_MAX_CLIENTS = 10
VEIL_SSL_ON = False
VEIL_WS_MAX_TIME_TO_WAIT = 15

# Pool parameters
# -----------------------------
MIX_POOL_SIZE = 1
MAX_POOL_SIZE = 200
MAX_VM_AMOUNT_IN_POOL = 1000

# Others
# -----------------------------
DEFAULT_NAME = 'Unknown'