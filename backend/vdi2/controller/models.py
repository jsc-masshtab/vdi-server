import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from database import db, get_list_of_values_from_db
from auth.utils import crypto


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

    @staticmethod
    async def get_controllers_addresses():
        return await get_list_of_values_from_db(Controller, Controller.address)

    @staticmethod
    async def get_controller_id_by_ip(ip_address):
        # controller = await Controller.query.where(Controller.address == ip_address).gino.first()
        return await Controller.select('id').where(Controller.address == ip_address).gino.scalar()

    @staticmethod
    async def get_token(uid: str):
        if not uid:
            raise AssertionError('Empty uid.')
        query = Controller.select('token').where(
            (Controller.expires_on >= datetime.now()) & (Controller.id == uid))
        return await query.gino.scalar()

    @staticmethod
    async def get_auth_info(uid: str):
        if not uid:
            raise AssertionError('Empty uid.')
        query = Controller.select('username', 'password', 'ldap_connection').where(Controller.id == uid)
        auth_info = await query.gino.first()
        username, encrypted_password, ldap_connection = auth_info
        password = crypto.decrypt(encrypted_password)
        return dict(username=username, password=password, ldap=ldap_connection)

    @staticmethod
    async def set_auth_info(uid: str, token: str, expires_on: datetime):
        """Сделано через staticmethod, чтобы не хранить инстанс.
        Гипотетически запись может измениться, пока мы получаем ответ. А так данные будут записываться по ip."""
        if not uid:
            raise AssertionError('Empty uid.')
        return await Controller.update.values(token=token, expires_on=expires_on).where(
            Controller.id == uid).gino.status()

    @staticmethod
    async def invalidate_auth(uid: str):
        if not uid:
            raise AssertionError('Empty uid.')
        return await Controller.update.values(token=None, expires_on=datetime.utcfromtimestamp(0)).where(
            Controller.id == uid).gino.status()
