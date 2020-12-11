from common.veil.veil_gino import AbstractSortableStatusModel
from common.database import db
from sqlalchemy.sql import func

import uuid
from sqlalchemy.dialects.postgresql import UUID


class ActiveTkConnection(db.Model, AbstractSortableStatusModel):
    """Таблица активных соединений тк по вебсокетам
    Неактульные данные удаляются из таблицы автоматом в классе ThinClientConnMonitor"""

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
    last_interaction = db.Column(db.DateTime(timezone=True))  # время когда
    # пользователь в последний раз тыкал клавиши или кликал мышь
    disconnected = db.Column(db.DateTime(timezone=True))  # Если это поле None, значит соединение активно

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

        await TkConnectionStatistics.create_tk_event(conn_id=model.id, message='Login')
        return model.id

    @staticmethod
    async def get_active_thin_clients_count():
        conn_count = await db.select([db.func.count()]).select_from(ActiveTkConnection).\
            where(ActiveTkConnection.disconnected == None).gino.scalar()  # noqa
        return conn_count

    @staticmethod
    async def get_vm_id(conn_id):
        vm_id = await ActiveTkConnection.select('vm_id').where((ActiveTkConnection.id == conn_id)).gino.scalar()
        return vm_id

    @staticmethod
    async def update_vm_id(conn_id, vm_id):
        await ActiveTkConnection.update.values(vm_id=vm_id, data_received=func.now()). \
            where(ActiveTkConnection.id == conn_id).gino.status()

        if vm_id:
            from common.models.vm import Vm
            vm = await Vm.get(vm_id)
            vm_verbose_name = vm.verbose_name if vm else ''
            message = 'Connected to VM {}'.format(vm_verbose_name)
        else:
            message = 'Disconnected from VM'

        await TkConnectionStatistics.create_tk_event(conn_id=conn_id, message=message)

    @staticmethod
    async def update_last_interaction(conn_id):
        await ActiveTkConnection.update.values(last_interaction=func.now(), data_received=func.now()). \
            where(ActiveTkConnection.id == conn_id).gino.status()

    async def deactivate(self):
        """Соединение неативно, когда у него выставлено время дисконнекта"""
        await self.update(disconnected=func.now()).apply()
        await TkConnectionStatistics.create_tk_event(conn_id=self.id, message='Logout')


class TkConnectionStatistics(db.Model, AbstractSortableStatusModel):
    """Накопленная статистика о соеднинении ТК.
    В данный момент фиксируется факты подключения/отключения к ВМ за время соединения
    Мб в будущем еще что-то добавим"""

    __tablename__ = 'tk_connection_statistis'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    conn_id = db.Column(UUID(), db.ForeignKey('active_tk_connection.id', ondelete="CASCADE"),
                        nullable=False, index=True)
    message = db.Column(db.Unicode(length=128))
    created = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    @staticmethod
    async def create_tk_event(conn_id, message):
        """Фиксировать подключение/отключение клиента к вм"""
        if not conn_id:
            return

        await TkConnectionStatistics.create(conn_id=conn_id, message=message)
