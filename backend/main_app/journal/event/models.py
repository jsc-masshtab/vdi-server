# -*- coding: utf-8 -*-
# TODO: удалять зависимые записи журнала событий, возможно через ON_DELETE
#  при удалении родительской сущности (нет явной связи, сами не удалятся).

import uuid
import json

from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database import db

from redis_broker import INTERNAL_EVENTS_CHANNEL, REDIS_CLIENT

from front_ws_api.subscription_sources import EVENTS_SUBSCRIPTION


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    event_type = db.Column(db.Integer(), nullable=False)
    message = db.Column(db.Unicode(length=256), nullable=False)
    description = db.Column(db.Unicode())
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    user = db.Column(db.Unicode(length=128), default='system')

    def __init__(self, **kw):
        super().__init__(**kw)
        self._read_by = set()
        self._entity = set()

    @property
    def read_by(self):
        return self._read_by

    @read_by.setter
    def add_read_by(self, user):
        self._read_by.add(user)

    @property
    def entity(self):
        return self._entity

    @entity.setter
    def add_entity(self, entity):
        self._entity.add(entity)

    @staticmethod
    async def mark_read_by(user_id, events_id_list):
        """Отмечаем список сообщений как прочитанные пользователем, если они ещё не
            Если списка нет, то отмечаем ВСЁ
        """
        if not events_id_list:
            results = await Event.select('id').gino.all()
            events_id_list = [value for value, in results]
        async with db.transaction():
            for event_id in events_id_list:
                # get_or_create
                filters = [(EventReadByUser.event == event_id), (EventReadByUser.user == user_id)]
                relation = await EventReadByUser.query.where(and_(*filters)).gino.first()
                if relation is None:
                    await EventReadByUser.create(event=event_id, user=user_id)

    @staticmethod
    async def unmark_read_by(user_id, events_id_list):
        """Убираем отметки о прочтении списка сообщений для пользователя
            Если списка нет, то убираем ВСЁ
        """
        # TODO: возможно, быстрее будет удалять список связей, а затем создавать новый, при связывании сущностей,
        #  нежели чем создавать связи по одной с проверкой на существование
        filters = [(EventReadByUser.user == user_id)]
        if events_id_list:
            filters.append((EventReadByUser.event.in_(events_id_list)))
        await EventReadByUser.delete.where(and_(*filters)).gino.status()

    @classmethod
    async def soft_create(cls, event_type, msg, description, user, entity_dict: dict):
        from auth.models import Entity
        async with db.transaction():  # noqa
            # 1. Создаем сам Евент
            event = await Event.create(
                event_type=event_type,
                message=msg,
                description=description,
                user=user
            )
            # 2. Создаем запись сущности
            if entity_dict and isinstance(entity_dict, dict):
                entity = await Entity.query.where(  # noqa
                    (Entity.entity_type == entity_dict['entity_type']) &  # noqa
                    (Entity.entity_uuid == entity_dict.get('entity_uuid'))  # noqa
                ).gino.first()  # noqa
                if not entity:
                    entity = await Entity.create(**entity_dict)
                # 3. Создаем связь
                await EventEntity.create(entity_id=entity.id, event_id=event.id)
            return True

    @classmethod
    async def create_event(cls, msg, event_type=0, description=None, user='system', entity_dict=None):
        from journal.log.logging import Logging
        msg_dict = dict(event_type=event_type,
                        message=msg,
                        user=user,
                        event='event',
                        resource=EVENTS_SUBSCRIPTION)
        if event_type == 0:
            Logging.logger_application_info(msg, description)
        elif event_type == 1:
            Logging.logger_application_warning(msg, description)
        elif event_type == 2:
            Logging.logger_application_error(msg, description)

        try:
            REDIS_CLIENT.publish(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))
        except TypeError: # Cant serialize
            pass
        await cls.soft_create(event_type, msg, description, user, entity_dict)


class EventEntity(db.Model):
    """Связывающая сущность"""
    __tablename__ = 'event_entities'
    event_id = db.Column(UUID(), db.ForeignKey('event.id'), nullable=False)
    entity_id = db.Column(UUID(), db.ForeignKey('entity.id'), nullable=False)


class EventReadByUser(db.Model):
    """Связывающая сущность"""
    __tablename__ = 'event_read_by_user'
    event = db.Column(UUID(), db.ForeignKey('event.id'), nullable=False)
    user = db.Column(UUID(), db.ForeignKey('user.id'), nullable=False)
