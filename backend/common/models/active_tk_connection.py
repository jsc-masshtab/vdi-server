# -*- coding: utf-8 -*-
import uuid

from sqlalchemy import (
    Enum as AlchemyEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import and_, func

from common.database import db
from common.models.auth import User
from common.models.pool import Pool
from common.veil.veil_gino import AbstractSortableStatusModel


class ActiveTkConnection(db.Model, AbstractSortableStatusModel):
    """Таблица соединений тк по вебсокетам."""

    __tablename__ = "active_tk_connection"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(UUID(), nullable=False)
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

    @classmethod
    async def soft_create(cls, conn_id, is_conn_init_by_user, **kwargs):
        """Создает/заменяет запись о соединении. Возвращает id."""
        model = await cls.get(conn_id) if conn_id else None

        # update
        if model:
            await model.update(**kwargs, data_received=func.now()).apply()
        else:
            model = await cls.create(**kwargs)

        if (
            is_conn_init_by_user
        ):  # Флаг чтобы различить инициировано ли соединение ползователем или это авторекконкт
            await model.update_last_interaction()

        user = await User.get(kwargs["user_id"])
        await TkConnectionStatistics.create_tk_event(
            conn_id=model.id, message="{} connected.".format(user.username)
        )
        return model

    @staticmethod
    async def get_thin_clients_conn_count(get_disconnected, user_id):

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

    async def update_vm_data(self, vm_id, conn_type, is_conn_secure):

        user = await User.get(self.user_id)

        from common.models.vm import Vm

        if vm_id:
            vm = await Vm.get(vm_id)
            vm_verbose_name = vm.verbose_name if vm else ""
            message = "{} connected to VM {}.".format(user.username, vm_verbose_name)
        else:
            vm = await Vm.get(self.vm_id)
            vm_verbose_name = vm.verbose_name if vm else ""
            message = "{} disconnected from VM {}.".format(
                user.username, vm_verbose_name
            )
        await TkConnectionStatistics.create_tk_event(conn_id=self.id, message=message)

        is_conn_secure = is_conn_secure if (is_conn_secure is not None) else False
        await self.update(vm_id=vm_id, connection_type=conn_type, is_connection_secure=is_conn_secure,
                          data_received=func.now()).apply()

    async def update_last_interaction(self):
        await self.update(last_interaction=func.now(), data_received=func.now()).apply()

    async def deactivate(self):
        """Соединение неативно, когда у него выставлено время дисконнекта."""
        await self.update(disconnected=func.now()).apply()
        user = await User.get(self.user_id)
        await TkConnectionStatistics.create_tk_event(
            conn_id=self.id, message="{} disconnected.".format(user.username)
        )


class TkConnectionStatistics(db.Model, AbstractSortableStatusModel):
    """Накопленная статистика о соеднинении ТК.

    В данный момент фиксируется факты подключения/отключения к ВМ за время соединения
    Мб в будущем еще что-то добавим.
    """

    __tablename__ = "tk_connection_statistics"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    conn_id = db.Column(
        UUID(),
        db.ForeignKey("active_tk_connection.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message = db.Column(db.Unicode(length=128))
    created = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    @staticmethod
    async def create_tk_event(conn_id, message):
        """Фиксировать подключение/отключение клиента к вм."""
        if not conn_id:
            return

        await TkConnectionStatistics.create(conn_id=conn_id, message=message)
