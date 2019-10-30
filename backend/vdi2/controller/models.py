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

    username = db.Column(db.Unicode(length=128), nullable=False)
    password = db.Column(db.Unicode(length=128), nullable=False)
    ldap_connection = db.Column(db.Boolean(), nullable=False, default=False)
    token = db.Column(db.Unicode(length=1024))
    expires_on = db.Column(db.DateTime(timezone=True))

    # TODO: purge hardcode
    @staticmethod
    async def get_token(controller_ip):
        return await Controller.select('token').where(
            (Controller.username == VEIL_CREDENTIALS['username']) & (
                    Controller.address == controller_ip)).gino.scalar()
