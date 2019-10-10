import uuid

from gino.ext.tornado import Gino
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

db = Gino()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
    email = db.Column(db.Unicode(length=256), unique=True)
    first_name = db.Column(db.Unicode(length=32))
    last_name = db.Column(db.Unicode(length=128))
    date_joined = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    last_login = db.Column(db.DateTime(timezone=True), server_default=func.now())
    is_superuser = db.Column(db.Boolean())
    is_active = db.Column(db.Boolean())


class Pool(db.Model):
    __tablename__ = 'pools'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False)
    status = db.Column(db.Unicode(length=128), nullable=False)
    controller = db.Column(UUID(as_uuid=True), db.ForeignKey('controllers.id'))
