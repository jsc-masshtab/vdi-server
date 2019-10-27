import uuid

from sqlalchemy.dialects.postgresql import UUID

from database import db
from settings import VEIL_CREDENTIALS


class Controller(db.Model):
    __tablename__ = 'controllers'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False)
    status = db.Column(db.Unicode(length=128))
    address = db.Column(db.Unicode(length=15), nullable=False)
    description = db.Column(db.Unicode(length=256))
    version = db.Column(db.Unicode(length=128))
    default = db.Column(db.Boolean())


class VeilCredentials(db.Model):
    __tablename__ = 'veil_creds'
    username = db.Column(db.Unicode(length=128), nullable=False)
    token = db.Column(db.Unicode(length=1024), nullable=False)
    controller_ip = db.Column(db.Unicode(length=100), nullable=False)
    expires_on = db.Column(db.DateTime(timezone=True), nullable=False)

    @staticmethod
    async def get_token(controller_ip):
        return await VeilCredentials.select('token').where(
            (VeilCredentials.username == VEIL_CREDENTIALS['username']) & (
                    VeilCredentials.controller_ip == controller_ip)).gino.scalar()
