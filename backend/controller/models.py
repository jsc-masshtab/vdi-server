import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from auth.utils import crypto
from controller.client import ControllerClient
from database import db, get_list_of_values_from_db, Status
from common.veil_errors import SimpleError
from event.models import Event
# TODO: validate token by expires_on parameter
# TODO: validate status


class Controller(db.Model):
    # TODO: indexes
    __tablename__ = 'controller'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    status = db.Column(db.Unicode(length=128))
    address = db.Column(db.Unicode(length=15), nullable=False, unique=True)
    description = db.Column(db.Unicode(length=256))
    version = db.Column(db.Unicode(length=128))

    username = db.Column(db.Unicode(length=128), nullable=False)
    password = db.Column(db.Unicode(length=128), nullable=False)
    ldap_connection = db.Column(db.Boolean(), nullable=False, default=False)
    token = db.Column(db.Unicode(length=1024))
    expires_on = db.Column(db.DateTime(timezone=True))  # Срок истечения токена.

    @property
    def pools_query(self):
        from pool.models import Pool  # Такой импорт из-за импорта в Pool модели Controller.

        pools_query = Controller.join(Pool).select().where(Controller.id == self.id)
        return pools_query

    @property
    async def has_pools(self):
        """Проверяем наличие пулов"""
        pools = await self.pools_query.gino.all()
        return True if pools else False

    @staticmethod
    async def get_controllers_addresses():
        return await get_list_of_values_from_db(Controller, Controller.address)

    @staticmethod
    async def get_controller_id_by_ip(ip_address):
        # controller = await Controller.query.where(Controller.address == ip_address).gino.first()
        return await Controller.select('id').where(Controller.address == ip_address).gino.scalar()

    @staticmethod
    async def get_token(ip_address: str):
        query = Controller.select('token', 'expires_on').where(Controller.address == ip_address)
        token_info = await query.gino.first()
        if token_info:
            token, expires_on = token_info
            if not token or not expires_on:
                token = await Controller.refresh_token(ip_address)
            elif expires_on < datetime.now(expires_on.tzinfo):
                token = await Controller.refresh_token(ip_address)
            return token
        else:
            raise AssertionError('No such controller')

    @staticmethod
    async def invalidate_auth(ip_address: str):
        return await Controller.update.values(
            token=None,
            expires_on=datetime.utcfromtimestamp(0)
        ).where(Controller.address == ip_address).gino.status()

    @staticmethod
    async def refresh_token(ip_address: str):
        # TODO: error handling
        # TODO: set controller status to BAD_AUTH

        query = Controller.select(
            'address',
            'username',
            'password',
            'ldap_connection'
        ).where(Controller.address == ip_address)

        controller = await query.gino.first()
        if controller:
            address, username, encrypted_password, ldap_connection = controller
            password = crypto.decrypt(encrypted_password)
            auth_info = dict(username=username, password=password, ldap=ldap_connection)
            controller_client = ControllerClient(address)
            token, expires_on = await controller_client.auth(auth_info=auth_info)
            await Controller.update.values(
                token=token,
                expires_on=expires_on
            ).where(Controller.address == ip_address).gino.status()
            return token
        else:
            raise AssertionError('No such controller')

    async def soft_delete(self):
        """Удаление сущности в статусе ACTIVE у которой нет зависимых сущностей"""

        if self.status != Status.ACTIVE.value:  # Value потому что Controller.status это обычный Varchar, а не Enum
            error_msg = 'Удаление не может быть выполнено из-за блокирующего статуса. Выполните форсированное удаление.'
            raise SimpleError(error_msg)

        controller_has_pools = await self.has_pools
        if controller_has_pools:
            raise SimpleError('У контроллера есть пулы виртуальных машин. Выполните полное удаление.')

        msg = 'Выполнено удаление контроллера {id}.'.format(id=self.id)
        await self.delete()
        await Event.create_info(msg)
        return True

    async def force_delete(self):
        """Удаление сущности независимо от статуса у которой нет зависимых сущностей"""

        controller_has_pools = await self.has_pools
        if controller_has_pools:
            raise SimpleError('У контроллера есть пулы виртуальных машин. Выполните полное удаление.')

        msg = 'Выполнено форсированное удаление контроллера {id}.'.format(id=self.id)
        await self.delete()
        await Event.create_info(msg)
        return True

    async def full_delete_pools(self):
        """Полное удаление пулов контроллера"""
        pools = await self.pools_query.gino.all()
        for pool in pools:
            await pool.full_delete(commit=False)

    async def full_delete(self):
        """Удаление сущности в статусе ACTIVE с удалением зависимых сущностей"""

        if self.status != Status.ACTIVE.value:
            error_msg = 'Удаление не может быть выполнено из-за блокирующего статуса. Выполните форсированное удаление.'
            raise SimpleError(error_msg)

        msg = 'Выполнено полное удаление контроллера {id}.'.format(id=self.id)
        await self.delete()
        await Event.create_info(msg)
        return True
