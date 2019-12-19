import uuid
from functools import partialmethod

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database import db
#from resources_monitoring.handlers import client_manager
from resources_monitoring.resources_monitoring_data import EVENTS_SUBSCRIPTION


class Event(db.Model):
    TYPE_INFO = 0
    TYPE_WARNING = 1
    TYPE_ERROR = 2

    __tablename__ = 'event'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    event_type = db.Column(db.Integer(), nullable=False)
    message = db.Column(db.Unicode(length=256), nullable=False)
    description = db.Column(db.Unicode())
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    user = db.Column(db.Unicode(length=128), default='system')

    @classmethod
    async def create_event(cls, msg, event_type=TYPE_INFO, description=None, user='system'):
        # TODO: build msg dict in an unified special format
        # TODO: connect with task and user entity
        # TODO: log event
        print(msg)
        msg_dict = dict(event_type=event_type,
                        message=msg,
                        user=user,
                        event='event?',
                        resource=EVENTS_SUBSCRIPTION)
        #await client_manager.send_message(msg_dict)
        await Event.create(
            event_type=event_type,
            message=msg,
            description=description,
            user=user
        )

    create_info = partialmethod(create_event, event_type=TYPE_INFO)
    create_warning = partialmethod(create_event, event_type=TYPE_WARNING)
    create_error = partialmethod(create_event, event_type=TYPE_ERROR)
