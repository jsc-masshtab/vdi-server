import uuid
from functools import partialmethod

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database import db


class Event(db.Model):
    TYPE_INFO = 0
    TYPE_WARNING = 1
    TYPE_ERROR = 2

    __tablename__ = 'event'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    event_type = db.Column(db.Integer(), nullable=False)
    message = db.Column(db.Unicode(length=256), nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    user = db.Column(db.Unicode(length=128), default='system')

    async def create_event(self, msg, event_type=TYPE_INFO, user='system'):
        await Event.create(
            event_type=event_type,
            message=msg,
            user=user
        )

    create_info = partialmethod(create_event, event_type=TYPE_INFO)
    create_warning = partialmethod(create_event, event_type=TYPE_WARNING)
    create_error = partialmethod(create_event, event_type=TYPE_ERROR)
