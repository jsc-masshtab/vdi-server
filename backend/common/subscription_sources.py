# -*- coding: utf-8 -*-
from enum import Enum

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


class WsEventToClient(Enum):
    CREATED = "CREATED"  # Создание сущности. Имя диктуется ws интерфейсом контроллера
    UPDATED = "UPDATED"  # Обновление сущности. Имя диктуется ws интерфейсом контроллера
    DELETED = "DELETED"  # Удаление сущности. Имя диктуется ws интерфейсом контроллера
    VM_PREPARATION_PROGRESS = "vm_preparation_progress"  # Прогресс подготовки ВМ перед выдачей клиенту
    POOL_ENTITLEMENT_CHANGED = "pool_entitlement_changed"  # Смена прав на пользование пулом


class WsMessageDirection(Enum):
    ADMIN_TO_USER = "admin_to_user"
    USER_TO_ADMIN = "user_to_admin"
