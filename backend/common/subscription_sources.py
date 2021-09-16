# -*- coding: utf-8 -*-
from enum import Enum

# Подписка на события на vdi брокере, относящиеся напрямую к тонкому клиенту Выделено в отдельный тип
# событий, так как они нужны только тонкому клиенту
EVENTS_THIN_CLIENT_SUBSCRIPTION = "/events_thin_client/"

# Подписка на события подключения/отключения тонких клиентов к vdi брокеру
THIN_CLIENTS_SUBSCRIPTION = "/thin_clients/"
USERS_SUBSCRIPTION = "/users/"
POOLS_SUBSCRIPTION = "/pools/"
# subscription to receive events
EVENTS_SUBSCRIPTION = "/events/"
# subscription to receive controller status
CONTROLLERS_SUBSCRIPTION = "/controllers/"
# subscription to receive VDI related task data
VDI_TASKS_SUBSCRIPTION = "/vdi_tasks/"
# subscriptions to receive data from controller
CONTROLLER_SUBSCRIPTIONS_LIST = [
    "/clusters/",
    "/resource_pools/",
    "/nodes/",
    "/data-pools/",
    "/domains/",
    "/tasks/",
]
# subscriptions to data which VDI front can receive from VDI back
VDI_FRONT_ALLOWED_SUBSCRIPTIONS_LIST = [  # FRONT == admin web interface
    *CONTROLLER_SUBSCRIPTIONS_LIST,
    THIN_CLIENTS_SUBSCRIPTION,
    USERS_SUBSCRIPTION,
    POOLS_SUBSCRIPTION,
    EVENTS_SUBSCRIPTION,
    CONTROLLERS_SUBSCRIPTION,
    VDI_TASKS_SUBSCRIPTION,
]


class SubscriptionCmd:
    add = "add"
    delete = "delete"


class WsMessageType(Enum):
    CONTROL = "control"
    DATA = "data"
    TEXT_MSG = "text_msg"
    UPDATED = "UPDATED"


class WsMessageDirection(Enum):
    ADMIN_TO_USER = "admin_to_user"
    USER_TO_ADMIN = "user_to_admin"
