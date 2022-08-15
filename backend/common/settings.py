# -*- coding: utf-8 -*-
"""Default project settings."""
import os


SETTINGS_PATH = os.path.dirname(__file__)

# Crypto settings
# -----------------------------
# Default values - not used in production.
SECRET_KEY = "RSrf948GB2YXQKBjXhikwxDDJbfooHoBuewQYqO1A2MyBqK15G"
FERNET_KEY = b"LRzSxWyxqKD4p2BR11-nVmghV67AVmQ4CxYi__S_OH8="

# Database settings
# -----------------------------

DB_HOST = os.getenv("VDI_BROKER_DB_HOST", "localhost")
DB_PORT = 5432
DB_NAME = "vdi"
DB_USER = "postgres"
DB_PASS = "postgres"

# Pool settings
POOL_MIN_SIZE = 1
POOL_MAX_SIZE = 10000
POOL_MAX_CREATE_ATTEMPTS = 15
DOMAIN_CREATION_MAX_STEP = 100

# Journal settings
DEBUG = False

# Auth settings
# -----------------------------
# Включает/выключает проверку токенов, стандартный интерфейс GraphQL становится недоступным/доступным
AUTH_ENABLED = True
# Локальная авторизация
LOCAL_AUTH = True
# Авторизация через внешние службы
EXTERNAL_AUTH = True
# Авторизация PAM исключает возможность использования LOCAL_AUTH
PAM_AUTH = not LOCAL_AUTH
PAM_TASK_TIMEOUT = 5
PAM_USER_ADD_CMD = "/usr/sbin/vdi_adduser_bi.sh"
PAM_GROUP_ADD_CMD = "/usr/sbin/vdi_addgroup_bi.sh"
PAM_USER_EDIT_CMD = "/usr/sbin/vdi_edituser_bi.sh"
PAM_USER_SET_PASS_CMD = "/usr/sbin/vdi_set_pass_bi.sh"
PAM_CHECK_IN_GROUP_CMD = "/usr/sbin/vdi_check_in_group_bi.sh"
PAM_USER_REMOVE_CMD = "/usr/sbin/vdi_remove_user_group_bi.sh"
PAM_SUDO_CMD = "/usr/bin/sudo"
PAM_KILL_PROC_CMD = "/usr/sbin/vdi_kill_proc_bi.sh"
PAM_USER_GROUP = "vdi-web"
PAM_SUPERUSER_GROUP = "vdi-web-admin"

MINIMUM_SUPPORTED_DESKTOP_THIN_CLIENT_VERSION = "1.13.2"

# JWT Options
# -----------------------------
JWT_EXPIRATION_DELTA = 86400
JWT_OPTIONS = {
    "verify_signature": True,
    "verify_exp": True,
    "verify_nbf": False,
    "verify_iat": True,
    "verify_aud": False,
}
JWT_AUTH_HEADER_PREFIX = "JWT"
JWT_ALGORITHM = "HS256"

# Websocket settings
# -----------------------------
WS_PING_INTERVAL = 10
WS_PING_TIMEOUT = 35

# ECP Veil settings
# -----------------------------
VEIL_REQUEST_TIMEOUT = 15
VEIL_CONNECTION_TIMEOUT = 15
VEIL_GUEST_AGENT_EXTRA_WAITING = 3
VEIL_GUEST_AGENT_WIN_PATH = "C:\\Program Files\\Qemu-ga\\"
VEIL_OPERATION_WAITING = 10
VEIL_MAX_BODY_SIZE = 1000 * 1024 ^ 3
VEIL_MAX_CLIENTS = 10
VEIL_SSL_ON = False
VEIL_WS_MAX_TIME_TO_WAIT = 60
VEIL_VM_PREPARE_TIMEOUT = 1200.0
VEIL_VM_REMOVE_TIMEOUT = 1200.0
VEIL_MAX_URL_LEN = 6000
VEIL_MAX_IDS_LEN = 3780
VEIL_MAX_VM_CREATE_ATTEMPTS = 10
VEIL_DEFAULT_VM_DISCONNECT_ACTION_TIMEOUT = 60  # Время, через которое над ВМ выполнится действие
# после дисконнекта пользователя, сек

# Cache settings
# -----------------------------
VEIL_CACHE_TTL = 1
VEIL_CACHE_SERVER = ("localhost", 11211)

# Locale settings
# -----------------------------
LANGUAGE = "ru"

# Others
# -----------------------------
DEFAULT_NAME = "-"
BROKER_NAME = "VeiL VDI"

# LDAP
# -----------------------------
LDAP_TIMEOUT = 20
LDAP_NETWORK_TIMEOUT = 15
LDAP_OPT_REFERRALS = 0
LDAP_LOGIN_PATTERN = "uid={username},cn=users,cn=accounts,{dc}"
OPENLDAP_LOGIN_PATTERN = "uid={username},ou=people,{dc}"

# File system paths
# -----------------------------
LOCALES_PATH = os.path.join(SETTINGS_PATH, "locales/")
LICENSE_PATH = os.path.join(SETTINGS_PATH, "../web_app/auth/license/")
SERIAL_KEY_FNAME = "serial.key"
PRIVATE_PEM_FNAME = "veil_vdi.pem"
PRIVATE_PEM_FPATH = os.path.join(LICENSE_PATH, PRIVATE_PEM_FNAME)
SERIAL_KEY_FPATH = os.path.join(LICENSE_PATH, SERIAL_KEY_FNAME)
SSL_KEY_FPATH = os.path.join(SETTINGS_PATH, "veil_ssl/veil_default.key")
SSL_CRT_FPATH = os.path.join(SETTINGS_PATH, "veil_ssl/veil_default.crt")

# Redis settings
# -----------------------------
REDIS_HOST = os.getenv("VDI_BROKER_REDIS_HOST", "localhost")
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = "4NZ7GpHn4IlshPhb"
REDIS_TIMEOUT = 5
REDIS_MAX_CLIENT_CONN = 200
REDIS_THIN_CLIENT_CMD_CHANNEL = (
    "TC_CMD_CHANNEL"
)  # канал для комманд обработчикам ws тонких клиентов.
# Команда по ws будет послана ТК
REDIS_TEXT_MSG_CHANNEL = (
    "TEXT_MSG_CHANNEL"
)  # Канал для обмена текстовыми сообщениями между админом и
# пользователями ТК
REDIS_ASYNC_TIMEOUT = 0.01
REDIS_RECONNECT_TIMEOUT = 5
REDIS_EXPIRE_TIME = 30  # Время хранения кэша, сек.

POOL_TASK_QUEUE = "POOL_TASK_QUEUE"  # Очередь задач воркера
POOL_WORKER_CMD_CHANNEL = (
    "POOL_WORKER_CMD_CHANNEL"
)  # Очередь для команд, которые принимаются пул воркером (Например,
# команда на отмену задачи)

WS_MONITOR_CHANNEL_OUT = (
    "WS_MONITOR_CHANNEL_OUT"
)  # канал для сообщений полученных монитором по ws от контроллеров
WS_MONITOR_CMD_QUEUE = (
    "WS_MONITOR_CMD_QUEUE"
)  # Очередь для команд, которые принимаются монитором ws.

INTERNAL_EVENTS_CHANNEL = "INTERNAL_EVENTS_CHANNEL"  # Канал для внутренних событий vdi

LOCK_TIMEOUT = 300  # Таймаут лока для недолгих операций

# VM manager settings
# -----------------------------
VM_MANGER_DATA_QUERY_INTERVAL = 60

try:
    from .local_settings import *  # noqa
except ImportError:
    pass
