import uuid
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Enum as SqlEnum

from database import db
# TODO: indexes


class ControllerUserType(Enum):
    LDAP = 0
    LOCAL = 1


class Controller(db.Model):
    __tablename__ = 'controller'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False)
    status = db.Column(db.Unicode(length=128))
    address = db.Column(db.Unicode(length=15), nullable=False)
    description = db.Column(db.Unicode(length=256))
    version = db.Column(db.Unicode(length=128))
    default = db.Column(db.Boolean())

    # TODO: save token
    # TODO: add credentials


class ControllerCredentials(db.Model):
    __tablename__ = 'controller_credentials'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    controller = db.Column(UUID(as_uuid=True), db.ForeignKey('controller.id'), nullable=False, unique=True)
    controller_user_type = db.Column(SqlEnum(ControllerUserType), nullable=False, default=ControllerUserType.LOCAL)
    username = db.Column(db.Unicode(length=128), nullable=False)
    password = db.Column(db.Unicode(length=128), nullable=False)
    token = db.Column(db.Unicode(length=1024), nullable=True)
    expires_on = db.Column(db.DateTime(), nullable=True)


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
