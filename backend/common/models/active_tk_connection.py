from common.veil.veil_gino import AbstractSortableStatusModel
from common.database import db
from sqlalchemy.sql import func

import uuid
from sqlalchemy.dialects.postgresql import UUID


class ActiveTkConnection(db.Model, AbstractSortableStatusModel):
    """Таблица активных соединений тк по вебсокетам"""

    __tablename__ = 'active_tk_connection'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(UUID(), unique=True)
    veil_connect_version = db.Column(db.Unicode(length=128))
    vm_id = db.Column(UUID())
    tk_ip = db.Column(db.Unicode(length=128))
    tk_os = db.Column(db.Unicode(length=128))
    connected = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    data_received = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    @staticmethod
    async def soft_create(user_id, veil_connect_version, vm_id, tk_ip, tk_os):
        """Создает/заменяет запись о соединении"""
        await ActiveTkConnection.delete.where(ActiveTkConnection.user_id == user_id).gino.status()
        await ActiveTkConnection.create(user_id=user_id,
                                        veil_connect_version=veil_connect_version,
                                        vm_id=vm_id,
                                        tk_ip=tk_ip,
                                        tk_os=tk_os)

    @staticmethod
    async def get_active_thin_clients_count():
        conn_count = await db.select([db.func.count()]).select_from(ActiveTkConnection).gino.scalar()
        return conn_count
