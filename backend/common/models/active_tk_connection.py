# -*- coding: utf-8 -*-
import uuid

from sqlalchemy import (
    Enum as AlchemyEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import and_, func

from common.database import db
from common.languages import lang_init
from common.log.journal import system_logger
from common.models.pool import AutomatedPool, Pool
from common.models.task import PoolTaskType
from common.models.vm import Vm
from common.subscription_sources import THIN_CLIENTS_SUBSCRIPTION
from common.veil.veil_gino import AbstractSortableStatusModel, Status
from common.veil.veil_redis import publish_data_in_internal_channel, request_to_execute_pool_task

from web_app.auth.license.utils import License


_ = lang_init()


class ActiveTkConnection(db.Model, AbstractSortableStatusModel):
    """Таблица соединений тк по вебсокетам."""

    __tablename__ = "active_tk_connection"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(UUID(), nullable=True)  # Сделан nullable=True для работы в режиме без авторизации
    veil_connect_version = db.Column(db.Unicode(length=128))
    vm_id = db.Column(UUID())
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

    connection_type = db.Column(AlchemyEnum(Pool.PoolConnectionTypes), nullable=True)  # тип подключения к ВМ
    is_connection_secure = db.Column(db.Boolean(), default=False, nullable=False)  # используется ли TLS

    # network stats overall (RDP/Spice). Текущие(последние) Характеристики взаимодействия ТК <-> ВМ
    read_speed = db.Column(db.Integer(), default=0)  # Скорость получения байт с ВМ на ТК
    write_speed = db.Column(db.Integer(), default=0)  # Отправка байт. Только для RDP. Спайс не дает эти данные
    avg_rtt = db.Column(db.Float(), default=0)
    loss_percentage = db.Column(db.Integer(), default=0)

    @classmethod
    async def soft_create(cls, conn_id, is_conn_init_by_user, **kwargs):
        """Создает/заменяет запись о соединении."""
        model = await cls.get(conn_id) if conn_id else None

        # update
        if model:
            await model.update(**kwargs, data_received=func.now()).apply()
            await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION, "UPDATED", model)
        else:
            model = await cls.create(**kwargs)
            await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION, "CREATED", model)

        if (
            is_conn_init_by_user
        ):  # Флаг чтобы различить инициировано ли соединение ползователем или это авторекконкт
            await model.update_last_interaction()

        return model

    @staticmethod
    async def get_thin_clients_conn_count(get_disconnected=False, user_id=None):

        query = db.select([db.func.count()]).select_from(ActiveTkConnection)

        filters = ActiveTkConnection.build_thin_clients_filters(get_disconnected, user_id)
        if filters:
            query = query.where(and_(*filters))

        conn_count = await query.gino.scalar()
        return conn_count

    @staticmethod
    async def get_vm_id(conn_id):
        vm_id = (
            await ActiveTkConnection.select("vm_id")
            .where((ActiveTkConnection.id == conn_id))
            .gino.scalar()
        )
        return vm_id

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

    async def recreation_guest_vm(self):
        vm = await Vm.get(self.vm_id)
        auto_pool = await AutomatedPool.get(vm.pool_id)

        if auto_pool.is_guest:
            vm = await Vm.get(self.vm_id)

            # Открепляем пользователя и устанавливаем статус "Удаляется"
            users = list()
            users.append(vm.user_id)
            await vm.remove_users(creator="system", users_list=users)
            await vm.update(status=Status.DELETING).apply()

            # Создаем таску пересоздания ВМ
            await request_to_execute_pool_task(
                vm.id, PoolTaskType.VM_GUEST_RECREATION,
                vm_id=str(vm.id)
            )

    async def update_vm_data(self, vm_id, conn_type, is_conn_secure):
        try:
            if not vm_id:
                await self.recreation_guest_vm()
        except Exception as e:
            await system_logger.debug("GUEST POOL EXPAND EXCEPTION: {}.".format(e))

        is_conn_secure = is_conn_secure if (is_conn_secure is not None) else False
        await self.update(vm_id=vm_id, connection_type=conn_type,
                          is_connection_secure=is_conn_secure,
                          data_received=func.now()).apply()

        # front ws notification
        await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION, "UPDATED",
                                               self)

    async def update_last_interaction(self):
        await self.update(last_interaction=func.now(), data_received=func.now()).apply()

    async def update_network_stats(self, **kwarg):
        conn_type = kwarg["connection_type"]

        read_speed = 0
        write_speed = 0
        avg_rtt = kwarg["avg_rtt"]
        # min_rtt = kwarg["min_rtt"]
        # max_rtt = kwarg["max_rtt"]
        loss_percentage = kwarg["loss_percentage"]

        if conn_type == Pool.PoolConnectionTypes.SPICE.name:
            read_speed = kwarg["total"]
        elif conn_type == Pool.PoolConnectionTypes.RDP.name:
            read_speed = kwarg["read_speed"]
            write_speed = kwarg["write_speed"]

        await self.update(read_speed=read_speed, write_speed=write_speed, avg_rtt=avg_rtt,
                          loss_percentage=loss_percentage, data_received=func.now()).apply()
        # front ws notification
        await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION, "UPDATED", self)

    async def deactivate(self):
        """Соединение неативно, когда у него выставлено время дисконнекта."""
        await self.update(disconnected=func.now()).apply()
        # front ws notification
        await publish_data_in_internal_channel(THIN_CLIENTS_SUBSCRIPTION, "UPDATED", self)

        try:
            if self.vm_id:
                await self.recreation_guest_vm()
        except Exception as e:
            await system_logger.debug("GUEST POOL EXPAND EXCEPTION: ", e)
