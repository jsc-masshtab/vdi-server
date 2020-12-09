from common.veil.veil_gino import AbstractSortableStatusModel
from common.database import db
from sqlalchemy.sql import func

import uuid
from sqlalchemy.dialects.postgresql import UUID


class ActiveTkConnection(db.Model, AbstractSortableStatusModel):
    """Таблица активных соединений тк по вебсокетам"""

    __tablename__ = 'active_tk_connection'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(UUID(), nullable=False)
    veil_connect_version = db.Column(db.Unicode(length=128))
    vm_id = db.Column(UUID())
    tk_ip = db.Column(db.Unicode(length=128))
    tk_os = db.Column(db.Unicode(length=128))
    connected = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    data_received = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())  # время когда
    # в последний раз ТК присылал какие-либо данные (ТК шлет их автоматически ответом на пинг например)
    last_interaction = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())  # время когда
    # пользователь в последний раз тыкал клавиши или кликал мышь

    @staticmethod
    async def soft_create(conn_id, user_id, veil_connect_version, vm_id, tk_ip, tk_os):
        """Создает/заменяет запись о соединении. Возвращает id"""

        model = await ActiveTkConnection.get(conn_id) if conn_id else None

        # update
        if model:
            await model.update(user_id=user_id,
                               veil_connect_version=veil_connect_version,
                               vm_id=vm_id,
                               tk_ip=tk_ip,
                               tk_os=tk_os).apply()

        else:
            model = await ActiveTkConnection.create(user_id=user_id,
                                                    veil_connect_version=veil_connect_version,
                                                    vm_id=vm_id,
                                                    tk_ip=tk_ip,
                                                    tk_os=tk_os)
        return model.id

    @staticmethod
    async def get_active_thin_clients_count():
        conn_count = await db.select([db.func.count()]).select_from(ActiveTkConnection).gino.scalar()
        return conn_count

    @staticmethod
    async def get_vm_id(conn_id):
        vm_id = await ActiveTkConnection.select('vm_id').where((ActiveTkConnection.id == conn_id)).gino.scalar()
        return vm_id
