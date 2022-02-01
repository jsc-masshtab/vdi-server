# -*- coding: utf-8 -*-
import uuid

from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from common.database import db
from common.models.pool import Pool
from common.veil.veil_gino import AbstractSortableStatusModel


class TkVmConnection(db.Model, AbstractSortableStatusModel):
    """Данные о подключении тк к ВМ.

    За время одного подключения к VDI пользователь может подключиться к
    нескольким ВМ. Поэтому выделяем в отдельную таблицу.
    """

    __tablename__ = "tk_vm_connection"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    tk_connection_id = db.Column(UUID(), db.ForeignKey("active_tk_connection.id", ondelete="CASCADE"),
                                 unique=False, nullable=False)

    successful = db.Column(db.Boolean(), nullable=False)  # Успешно ли было подключение
    conn_error_str = db.Column(db.Unicode(), nullable=True)  # Строка с сообщением об ошибке подключения,
    # если такая была

    vm_id = db.Column(UUID(), nullable=False)
    connected_to_vm = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())  # Время
    # подключения/попытки подключения к ВМ (последнее)
    disconnected_from_vm = db.Column(db.DateTime(timezone=True), nullable=True)  # Время
    # отключения от ВМ (последнее)

    connection_type = db.Column(AlchemyEnum(Pool.PoolConnectionTypes), nullable=True)  # тип подключения к ВМ
    is_connection_secure = db.Column(db.Boolean(), nullable=True)  # используется ли TLS

    # network stats overall (RDP/Spice). Текущие(последние) Характеристики взаимодействия ТК <-> ВМ
    read_speed = db.Column(db.Integer(), default=0)  # Скорость получения байт с ВМ на ТК
    write_speed = db.Column(db.Integer(), default=0)  # Отправка байт. Только для RDP. Спайс не дает эти данные
    avg_rtt = db.Column(db.Float(), default=0)
    loss_percentage = db.Column(db.Integer(), default=0)

    async def deactivate(self):
        await self.update(disconnected_from_vm=func.now()).apply()

    @staticmethod
    async def get_active_vm_conn(vm_id, tk_conn_id):
        """Получить запись об ативном соединении с ВМ."""
        model = await TkVmConnection.query.where((TkVmConnection.vm_id == vm_id) &  # noqa
                                                 (TkVmConnection.tk_connection_id == tk_conn_id) &  # noqa
                                                 (TkVmConnection.successful == True) &  # noqa
                                                 (TkVmConnection.disconnected_from_vm == None)).gino.first()  # noqa
        return model

    @classmethod
    async def soft_create(cls, vm_id, tk_connection_id, **kwargs):

        model = await TkVmConnection.get_active_vm_conn(vm_id, tk_connection_id)

        if model:  # update
            await model.update(**kwargs).apply()
        else:
            model = await cls.create(vm_id=vm_id,
                                     tk_connection_id=tk_connection_id,
                                     **kwargs)

        return model
