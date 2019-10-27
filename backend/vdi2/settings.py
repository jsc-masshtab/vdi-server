# -*- coding: utf-8 -*-
"""Project settings."""

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
WS_PING_INTERVAL = 1  # TODO: change to 6

# ECP Veil settings
# -----------------------------
VEIL_CREDENTIALS = dict(username='vdi', password='veil')
VEIL_REQUEST_TIMEOUT = 15
VEIL_CONNECTION_TIMEOUT = 15
VEIL_MAX_BODY_SIZE = 10 * 1024 ^ 3
VEIL_MAX_CLIENTS = 10
VEIL_SSL_ON = False
