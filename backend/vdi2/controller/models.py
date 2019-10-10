import uuid

from sqlalchemy.dialects.postgresql import UUID

from database import db


class Controller(db.Model):
    __tablename__ = 'controllers'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False)
    status = db.Column(db.Unicode(length=128))
    address = db.Column(db.Unicode(length=15), nullable=False)
    description = db.Column(db.Unicode(length=256))
    version = db.Column(db.Unicode(length=128))
    default = db.Column(db.Boolean())
