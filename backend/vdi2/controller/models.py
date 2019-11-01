import uuid
from sqlalchemy.dialects.postgresql import UUID

from database import db, get_list_of_values_from_db


class Controller(db.Model):
    # TODO: indexes
    __tablename__ = 'controller'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False)
    status = db.Column(db.Unicode(length=128))
    address = db.Column(db.Unicode(length=15), nullable=False)
    description = db.Column(db.Unicode(length=256))
    version = db.Column(db.Unicode(length=128))

    username = db.Column(db.Unicode(length=128), nullable=False)
    password = db.Column(db.Unicode(length=128), nullable=False)
    ldap_connection = db.Column(db.Boolean(), nullable=False, default=False)
    token = db.Column(db.Unicode(length=1024))
    expires_on = db.Column(db.DateTime(timezone=True))

    @staticmethod
    async def get_controllers_addresses():
        return await get_list_of_values_from_db(Controller, Controller.address)


# class VeilCredentials(db.Model):
#     __tablename__ = 'veil_creds'
#     username = db.Column(db.Unicode(length=128), nullable=False)
#     token = db.Column(db.Unicode(length=1024), nullable=Екгу)
#     controller_ip = db.Column(db.Unicode(length=100), nullable=False)
#     expires_on = db.Column(db.DateTime(timezone=True), nullable=False)
#
#     @staticmethod
#     async def get_token(controller_ip):
#         return await VeilCredentials.select('token').where(
#             (VeilCredentials.username == VEIL_CREDENTIALS['username']) & (
#                     VeilCredentials.controller_ip == controller_ip)).gino.scalar()


