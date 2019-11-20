import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from auth.utils import crypto
from controller.client import ControllerClient
from database import db, get_list_of_values_from_db


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

    @staticmethod
    async def get_controllers_addresses():
        return await get_list_of_values_from_db(Controller, Controller.address)

    @staticmethod
    async def get_controller_id_by_ip(ip_address):
        # controller = await Controller.query.where(Controller.address == ip_address).gino.first()
        return await Controller.select('id').where(Controller.address == ip_address).gino.scalar()


    @staticmethod
    async def get_token(ip_address: str):
        query = Controller.select('token', 'expires_on').where((Controller.address == ip_address))
        token_info = await query.gino.scalar()
        if token_info:
            token, expires_on = token_info
            if expires_on < datetime.now() or not token:
                token = Controller.refresh_token(ip_address)
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
        # TODO: check if token already refreshed?

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
