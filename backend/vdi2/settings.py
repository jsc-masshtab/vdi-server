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
credentials = dict(username='vdi', password='4ever')

# Pool parameters
# -----------------------------
MIX_POOL_SIZE = 1
MAX_POOL_SIZE = 200
MAX_VM_AMOUNT_IN_POOL = 1000

# Others
# -----------------------------
DEFAULT_NAME = 'Unknown'