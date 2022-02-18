# -*- coding: utf-8 -*-
import uuid
from enum import Enum

from sqlalchemy import desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import and_, func

from common.database import db
from common.languages import _local_
from common.log.journal import system_logger
from common.models.auth import User
from common.models.pool import Pool
from common.models.tk_vm_connection import TkVmConnection
from common.models.vm import Vm
from common.subscription_sources import THIN_CLIENTS_SUBSCRIPTION
from common.veil.veil_gino import AbstractSortableStatusModel
from common.veil.veil_redis import (
    publish_data_in_internal_channel
)

from web_app.auth.license.utils import License


class TkConnectionEvent(Enum):
    """События от ТК."""

    VM_CHANGED = "vm_changed"  # ВМ изменилась (подключение/отключение). Outdated.
    # Оставлено для поддержки тонких клиентов до версии 1.10.0 включительно

    VM_CONNECTED = "vm_connected"  # Клиент подключился к ВМ
    VM_DISCONNECTED = "vm_disconnected"  # Клиент отключился от ВМ
    VM_CONNECTION_ERROR = "vm_connection_error"  # Не удалось подключиться к ВМ
    CONNECTION_CLOSED = "connection_closed"  # Соединение с сервером VDI завершилось
    USER_GUI = "user_gui"  # Юзер нажал кнопку/кликнул
    NETWORK_STATS = "network_stats"  # Обновление сетевой статистики


class TkConnectionEventOut(Enum):
    """События, отправляемые тонкому клиенту."""

    VM_PREPARATION_PROGRESS = "vm_preparation_progress"  # Прогресс подготовки ВМ перед выдачей клиенту
    POOL_ENTITLEMENT_CHANGED = "pool_entitlement_changed"  # Измение прав на пользование пулом


class ActiveTkConnection(db.Model, AbstractSortableStatusModel):
    """Таблица соединений тк по вебсокетам."""

    __tablename__ = "active_tk_connection"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(UUID(), nullable=True)  # Сделан nullable=True для работы в режиме без авторизации
    veil_connect_version = db.Column(db.Unicode(length=128))

    tk_ip = db.Column(db.Unicode(length=128))
    tk_os = db.Column(db.Unicode(length=128))

    connected = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    data_received = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )  # время когда
    # в последний раз ТК присылал какие-либо данные (ТК шлет их автоматически ответом на пинг например)
    last_interaction = db.Column(db.DateTime(timezone=True))  # время когда
    # пользователь в последний раз тыкал клавиши или кликал мышь
    disconnected = db.Column(
        db.DateTime(timezone=True)
    )  # Если это поле None, значит соединение активно

    # additional data about client machine
    mac_address = db.Column(db.Unicode(length=128), nullable=True)
    hostname = db.Column(db.Unicode(length=128), nullable=True)

    @classmethod
    async def soft_create(cls, conn_id, is_conn_init_by_user, **kwargs):
        """Создает/заменяет запись о соединении."""
        model = await cls.get(conn_id) if conn_id else None

        # update
        if model:
            await model.update(**kwargs, data_received=func.now()).apply()
            await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION,
                                                   "UPDATED",
                                                   model)
        else:
            model = await cls.create(**kwargs)
            await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION,
                                                   "CREATED",
                                                   model)

        if (
            is_conn_init_by_user
        ):  # Флаг чтобы различить инициировано ли соединение ползователем или это автореконнект
            await model.update_last_interaction()

        return model

    @staticmethod
    async def get_thin_clients_conn_count(get_disconnected=False, user_id=None):

        query = db.select([db.func.count()]).select_from(ActiveTkConnection)

        filters = ActiveTkConnection.build_thin_clients_filters(get_disconnected,
                                                                user_id)
        if filters:
            query = query.where(and_(*filters))

        conn_count = await query.gino.scalar()
        return conn_count

    @staticmethod
    def build_thin_clients_filters(get_disconnected, user_id):
        filters = []
        # Если get_disconnected == false, то берем только активные соединения (disconnected == None)
        if not get_disconnected:
            filters.append(ActiveTkConnection.disconnected == None)  # noqa
        if user_id:
            filters.append(ActiveTkConnection.user_id == user_id)

        return filters

    @classmethod
    async def thin_client_limit_exceeded(cls):

        current_license = License()
        current_clients_count = await ActiveTkConnection.get_thin_clients_conn_count()
        return current_clients_count >= current_license.thin_clients_limit

    async def get_username(self):
        user = await User.get(self.user_id) if self.user_id else None
        username = user.username if user else "unknown"
        return username

    async def get_last_connected_vm_id(self):
        """Последняя ВМ, к которой произошло подключение."""
        query = TkVmConnection.query.where(TkVmConnection.tk_connection_id == self.id).\
            order_by(desc(TkVmConnection.connected_to_vm))

        tk_vm_conn = await query.gino.first()
        if tk_vm_conn:
            return tk_vm_conn.vm_id
        else:
            return None

    async def update_vm_data(self, tk_event_type, vm_id, conn_type, is_conn_secure):

        username = await self.get_username()
        await self.update(data_received=func.now()).apply()

        vm = await Vm.get(vm_id)
        if vm is None:
            return
        vm_verbose_name = vm.verbose_name
        vm_entity = vm.entity

        if tk_event_type == TkConnectionEvent.VM_CONNECTED.value:
            # Запись о подключении к ВМ
            await TkVmConnection.soft_create(vm_id=vm_id, tk_connection_id=self.id,
                                             connection_type=conn_type, is_connection_secure=is_conn_secure,
                                             successful=True, conn_error_str=None,
                                             connected_to_vm=func.now(),
                                             disconnected_from_vm=None)
            log_msg = _local_("User {} connected to VM {}.").format(username, vm_verbose_name)
            await system_logger.info(log_msg, entity=vm_entity, user=username)

        elif tk_event_type == TkConnectionEvent.VM_DISCONNECTED.value:
            #  Выставляем время отключения (Подключения имеющие время отключения считаются завершенными)

            tk_vm_conn = await TkVmConnection.get_active_vm_conn(vm_id, self.id)
            if tk_vm_conn:
                await tk_vm_conn.deactivate()
                log_msg = _local_("User {} disconnected from VM {}.").format(username, vm_verbose_name)
                await system_logger.info(log_msg, entity=vm_entity, user=username)
        else:
            return

        # front ws notification
        additional_data = dict(tk_conn_event=tk_event_type, vm_id=str(vm_id))
        await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION, "UPDATED", self,
                                               additional_data)

    async def update_vm_data_on_error(self, vm_id, connection_type, conn_error_code, conn_error_str):
        """Обновляем когда пользователь не смог подключиться к ВМ."""
        username = await self.get_username()
        vm = await Vm.get(vm_id)

        # Запись о неудачном подключении
        await TkVmConnection.soft_create(vm_id=vm_id, connection_type=connection_type,
                                         successful=False, connected_to_vm=func.now(),
                                         tk_connection_id=self.id, conn_error_str=conn_error_str)

        # log
        if vm:
            await system_logger.info(
                _local_("User {} failed to connect to VM {}.").format(username, vm.verbose_name),
                user=username,
                description=_local_("Error code: {}. Error message: {}.").format(
                    conn_error_code, conn_error_str)
            )

    async def update_last_interaction(self):
        await self.update(last_interaction=func.now(), data_received=func.now()).apply()

    async def update_network_stats(self, **kwarg):

        vm_id = kwarg.get("vm_id")
        if vm_id is None:
            return

        conn_type = kwarg["connection_type"]

        read_speed = 0
        write_speed = 0
        avg_rtt = kwarg["avg_rtt"]

        loss_percentage = kwarg["loss_percentage"]

        if conn_type == Pool.PoolConnectionTypes.SPICE.name:
            read_speed = kwarg["total"]
        elif conn_type == Pool.PoolConnectionTypes.RDP.name:
            read_speed = kwarg["read_speed"]
            write_speed = kwarg["write_speed"]

        tk_vm_conn = await TkVmConnection.get_active_vm_conn(vm_id, self.id)
        if tk_vm_conn:
            await tk_vm_conn.update(read_speed=read_speed,
                                    write_speed=write_speed,
                                    avg_rtt=avg_rtt,
                                    loss_percentage=loss_percentage).apply()

    async def deactivate(self, dead_connection_detected=False):
        """Соединение неактивно, когда у него выставлено время дисконнекта."""
        await self.update(disconnected=func.now()).apply()
        # Помечаем соединения с ВМ как завершенные (disconnected_from_vm != None)
        await TkVmConnection.update.values(disconnected_from_vm=func.now()).where(
            TkVmConnection.tk_connection_id == self.id).gino.status()

        # send event
        additional_data = dict(tk_conn_event=TkConnectionEvent.CONNECTION_CLOSED.value,
                               dead_connection_detected=dead_connection_detected)
        await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION, "UPDATED", self, additional_data)
