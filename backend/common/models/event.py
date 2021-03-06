# -*- coding: utf-8 -*-
# TODO: удалять зависимые записи журнала событий, возможно через ON_DELETE
#  при удалении родительской сущности (нет явной связи, сами не удалятся).

import csv
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import and_, between
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from common.database import db
from common.languages import _local_
from common.settings import INTERNAL_EVENTS_CHANNEL
from common.subscription_sources import EVENTS_SUBSCRIPTION, WsEventToClient, WsMessageType
from common.utils import gino_model_to_json_serializable_dict
from common.veil.veil_redis import publish_to_redis


class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    event_type = db.Column(db.Integer(), nullable=False)
    message = db.Column(db.Unicode(length=256), nullable=False)
    description = db.Column(db.Unicode())
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    user = db.Column(db.Unicode(length=128), default="system")
    entity_id = db.Column(UUID(), db.ForeignKey("entity.id"), default=uuid.uuid4)

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
    async def event_export(start, finish, journal_path):
        """Экспорт журнала по заданному временному периоду.

        :param start: начало периода ('2020-07-01T00:00:00.000001Z')
        :param finish: окончание периода ('2020-07-31T23:59:59.000001Z')
        :param journal_path: путь для экспорта ('/tmp/')
        """
        from common.veil.veil_errors import SilentError, SimpleError

        start_date = datetime.date(start)
        finish_date = datetime.date(finish)
        real_path = Path(journal_path)

        query = await Event.query.where(
            between(
                Event.created, start + timedelta(hours=3), finish + timedelta(hours=3)
            )
        ).gino.all()
        if not query:
            raise SilentError(_local_("Journal in this period is empty."))

        export = []
        for event in query:
            export.append(event.__values__)

        csv_name = "events_{}-{}.csv".format(
            start_date + timedelta(days=1), finish_date
        )
        name = real_path / csv_name
        try:
            with open("{}".format(name), "w") as f:
                writer = csv.DictWriter(f, fieldnames=export[0])
                writer.writeheader()
                for row in export:
                    writer.writerow(row)
        except FileNotFoundError:
            raise SilentError(_local_("Path {} is incorrect.").format(real_path))
        except IndexError:
            raise SilentError(
                _local_("Check date. Interval {} - {} is incorrect.").format(
                    start_date + timedelta(days=1), finish_date
                )
            )
        except MemoryError:
            raise SilentError(_local_("Not enough free space."))
        except Exception as e:
            raise SimpleError(_local_("Journal export error."), description=e)

        return name

    @staticmethod
    async def mark_read_by(user_id, events_id_list):
        """Отмечаем список сообщений как прочитанные пользователем, если они ещё не.

        Если списка нет, то отмечаем ВСЁ.
        """
        if not events_id_list:
            results = await Event.select("id").gino.all()
            events_id_list = [value for value, in results]
        async with db.transaction():
            for event_id in events_id_list:
                # get_or_create
                filters = [
                    (EventReadByUser.event == event_id),
                    (EventReadByUser.user == user_id),
                ]
                relation = await EventReadByUser.query.where(
                    and_(*filters)
                ).gino.first()
                if relation is None:
                    await EventReadByUser.create(event=event_id, user=user_id)

    @staticmethod
    async def unmark_read_by(user_id, events_id_list):
        """Убираем отметки о прочтении списка сообщений для пользователя.

        Если списка нет, то убираем ВСЁ.
        """
        # TODO: возможно, быстрее будет удалять список связей, а затем создавать новый, при связывании сущностей,
        #  нежели чем создавать связи по одной с проверкой на существование
        filters = [(EventReadByUser.user == user_id)]
        if events_id_list:
            filters.append((EventReadByUser.event.in_(events_id_list)))
        await EventReadByUser.delete.where(and_(*filters)).gino.status()

    @classmethod
    async def soft_create(cls, event_type, msg, description, user, entity_dict: dict):
        from common.models.auth import Entity

        async with db.transaction():  # noqa
            # 1. Создаем запись сущности
            if entity_dict and isinstance(entity_dict, dict):
                entity = await Entity.create(**entity_dict)
                # 2. Создаем Евент
                event = await Event.create(  # noqa
                    event_type=event_type,
                    message=msg,
                    description=description,
                    user=user,
                    entity_id=entity.id,
                )
            return event

    @classmethod
    async def create_event(
        cls, msg, event_type, description, user, entity_dict
    ):  # noqa

        msg_dict = dict(
            event_type=event_type,
            event=WsEventToClient.EVENT.value,
            resource=EVENTS_SUBSCRIPTION,
            msg_type=WsMessageType.DATA.value,
        )

        event_obj = await cls.soft_create(
            event_type, msg, description, user, entity_dict
        )
        msg_dict.update(gino_model_to_json_serializable_dict(event_obj))

        try:
            await publish_to_redis(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))
        except (TypeError):  # Can`t serialize
            pass


class EventReadByUser(db.Model):
    """Связывающая сущность."""

    __tablename__ = "event_read_by_user"
    event = db.Column(UUID(), db.ForeignKey("event.id"), nullable=False)
    user = db.Column(UUID(), db.ForeignKey("user.id"), nullable=False)


class JournalSettings(db.Model):
    __tablename__ = "journal_settings"
    id = db.Column(UUID(), primary_key=True)
    interval = db.Column(db.Unicode(length=128), nullable=False)
    period = db.Column(db.Unicode(length=128), nullable=False)
    form = db.Column(db.Unicode(length=128), nullable=False)
    duration = db.Column(db.Integer(), nullable=False)
    by_count = db.Column(db.Boolean(), nullable=False)
    count = db.Column(db.Integer(), nullable=False)
    dir_path = db.Column(db.Unicode(length=128), nullable=False)
    create_date = db.Column(db.DateTime(timezone=True), nullable=False)

    @classmethod
    async def change_journal_settings(
        cls,
        creator: str = "system",
        dir_path: str = None,
        period: str = None,
        by_count: bool = None,
        count: int = None,
        **kwargs
    ):
        from common.log.journal import system_logger
        from common.veil.veil_errors import SilentError

        settings = dict()
        if dir_path:
            settings["dir_path"] = dir_path
        if period and not by_count:
            settings["by_count"] = by_count
            if period == "day":
                settings["period"] = period
                settings["interval"] = "1 day"
                settings["form"] = "YYYY_MM_DD"
                settings["duration"] = 1095
            elif period == "week":
                settings["period"] = period
                settings["interval"] = "1 week"
                settings["form"] = "YYYY_MM_DD"
                settings["duration"] = 156
            elif period == "month":
                settings["period"] = period
                settings["interval"] = "1 month"
                settings["form"] = "YYYY_MM"
                settings["duration"] = 36
            elif period == "year":
                settings["period"] = period
                settings["interval"] = "1 year"
                settings["form"] = "YYYY"
                settings["duration"] = 3
            else:
                raise SilentError(_local_("Choose right period."))
        if by_count and count:
            settings["by_count"] = by_count
            if count > 1:
                settings["count"] = count
            else:
                raise SilentError(_local_("Count must be more than 1."))
        await cls.update.values(**settings).gino.status()
        entity = {"entity_type": "SECURITY", "entity_uuid": None}
        await system_logger.info(
            _local_("Journal settings changed."),
            description=settings,
            entity=entity,
            user=creator,
        )
