# -*- coding: utf-8 -*-
import uuid

from sqlalchemy import Enum as AlchemyEnum, and_
from sqlalchemy.dialects.postgresql import UUID

from common.database import db
from common.languages import _local_
from common.log.journal import system_logger
from common.models.pool import Pool
from common.models.vm import Vm
from common.veil.veil_gino import AbstractSortableStatusModel


class VmConnectionData(db.Model, AbstractSortableStatusModel):
    """Данные для подключения к ВМ."""

    __tablename__ = "vm_connection_data"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    vm_id = db.Column(UUID(), db.ForeignKey("vm.id", ondelete="CASCADE"), nullable=False)
    connection_type = db.Column(AlchemyEnum(Pool.PoolConnectionTypes), nullable=False)
    address = db.Column(db.Unicode(length=128), nullable=False)
    port = db.Column(db.Integer(), nullable=False)
    active = db.Column(db.Boolean(), nullable=False, default=True)  # Использовать ли данные для подключения

    @classmethod
    async def soft_create(cls, creator, **kwargs):
        vm_connection_data = await VmConnectionData.create(**kwargs)

        vm = await Vm.get(kwargs["vm_id"])
        connection_type = kwargs["connection_type"]
        await system_logger.info(
            _local_(f"Vm connection data for VM {vm.verbose_name} and connection type {connection_type} added"),
            user=creator,
            description=_local_(f" Kwargs: {kwargs}")
        )

        return vm_connection_data

    async def soft_update(self, creator, **kwargs):
        await VmConnectionData.update.values(**kwargs).gino.status()

        vm = await Vm.get(self.vm_id)
        await system_logger.info(
            _local_(f"Vm connection data for VM {vm.verbose_name} and connection type {self.connection_type} updated"),
            user=creator,
            description=_local_(f" Kwargs: {kwargs}")
        )

    async def soft_delete(self, creator):
        await self.delete()

        vm = await Vm.get(self.vm_id)
        await system_logger.info(
            _local_(f"Vm connection data for VM {vm.verbose_name} and connection type {self.connection_type} deleted"),
            user=creator
        )

    @staticmethod
    def get_vm_connection_data_list_query(vm_id):
        where_conditions = [
            VmConnectionData.vm_id == vm_id
        ]

        query = VmConnectionData.query.where(and_(*where_conditions))
        return query

    @staticmethod
    def build_where_list(vm_id, connection_type, active=None):
        where_conditions = list()
        if vm_id:
            where_conditions.append(VmConnectionData.vm_id == vm_id)
        if connection_type:
            where_conditions.append(VmConnectionData.connection_type == connection_type)
        if active is not None:
            where_conditions.append(VmConnectionData.active == active)

        return where_conditions

    @staticmethod
    async def reset_active(vm_id, connection_type):
        """Сбросить флаг active для всех пар vm_id<->connection_type."""
        where_conditions = VmConnectionData.build_where_list(vm_id, connection_type)
        await VmConnectionData.update.values(active=False).where(and_(*where_conditions)).gino.status()

    @staticmethod
    async def get_with_params(vm_id, connection_type, active=None):
        """Вернуть первую запись с указанными параметрами."""
        where_conditions = VmConnectionData.build_where_list(vm_id, connection_type, active)
        first = await VmConnectionData.query.where(and_(*where_conditions)).gino.first()
        return first
