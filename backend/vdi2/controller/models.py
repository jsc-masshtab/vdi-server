import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from database import db


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
    expires_on = db.Column(db.DateTime(timezone=True))  # Срок истечения токена.

    @staticmethod
    async def get_token(controller_ip):
        if not controller_ip:
            return
        query = Controller.select('token').where(
            (Controller.address == controller_ip) & (Controller.expires_on <= datetime.now()))
        return await query.gino.scalar()

