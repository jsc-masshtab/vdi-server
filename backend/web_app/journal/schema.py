# -*- coding: utf-8 -*-
from datetime import datetime

import graphene

from graphql import GraphQLError

from sqlalchemy import and_, desc, text

from veil_api_client import VeilRestPaginator

from common.database import db
from common.graphene_utils import ShortString
from common.languages import _local_
from common.log.journal import system_logger
from common.models.auth import Entity
from common.models.controller import ControllerFetcher
from common.models.event import Event, EventReadByUser, JournalSettings
from common.settings import DEFAULT_NAME
from common.utils import extract_ordering_data
from common.veil.veil_decorators import administrator_required, operator_required
from common.veil.veil_errors import SimpleError
from common.veil.veil_graphene import VeilEventTypeEnum, VeilResourceType

from web_app.auth.user_schema import User, UserType


def build_filters(
    event_type, start_date, end_date, user, read_by, entity_type, entity=None
):
    filters = []
    if event_type is not None:
        filters.append((Event.event_type == event_type))
    if start_date:
        filters.append((Event.created >= start_date))
    if end_date:
        filters.append((Event.created <= end_date))
    if user:
        filters.append((Event.user == user))
    if entity_type:
        filters.append((Entity.entity_type == entity_type))
    if entity:
        filters.append((Event.entity_id == entity))

    return filters


class EntityType(graphene.ObjectType):
    id = graphene.UUID()
    entity_uuid = graphene.UUID()
    entity_type = graphene.Field(ShortString)


class EventType(graphene.ObjectType):
    id = graphene.UUID()
    event_type = graphene.Int()
    message = graphene.Field(ShortString)
    description = graphene.Field(graphene.String)
    created = graphene.DateTime()
    user = graphene.Field(ShortString)
    read_by = graphene.List(UserType)
    entity = graphene.List(EntityType)
    entity_types = graphene.List(ShortString)
    entity_id = graphene.UUID()


class VeilEventType(VeilResourceType):
    id = graphene.UUID()
    event_type = graphene.Int()
    message = graphene.Field(ShortString)
    description = graphene.Field(graphene.String)
    created = graphene.DateTime()
    user = graphene.Field(ShortString)


class JournalSettingsType(graphene.ObjectType):
    id = graphene.UUID()
    interval = graphene.Field(ShortString)
    period = graphene.Field(ShortString)
    form = graphene.Field(ShortString)
    duration = graphene.Int()
    by_count = graphene.Boolean()
    count = graphene.Int()
    dir_path = graphene.Field(ShortString)
    create_date = graphene.DateTime()


class EventQuery(graphene.ObjectType):
    count = graphene.Int(
        event_type=graphene.Int(),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        user=ShortString(),
        read_by=graphene.UUID(),
        entity_type=ShortString(),
        entity=graphene.UUID(),
    )

    events = graphene.List(
        lambda: EventType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        event_type=graphene.Int(),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        user=ShortString(),
        read_by=graphene.UUID(),
        entity=graphene.UUID(),
        entity_type=ShortString(),
        ordering=ShortString(),
    )

    event = graphene.Field(lambda: EventType, id=graphene.UUID())

    entity_types = graphene.List(
        ShortString,
        event_type=graphene.Int(),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        user=ShortString(),
        read_by=graphene.UUID(),
        entity_type=ShortString(),
    )

    users = graphene.List(
        lambda: UserType,
        username=ShortString(),
        id=graphene.UUID()
    )

    veil_events_count = graphene.Int(event_type=graphene.Int(),
                                     controller=graphene.UUID())
    veil_events = graphene.List(
        lambda: VeilEventType,
        ordering=ShortString(),
        event_type=graphene.Int(),
        controller=graphene.UUID(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )

    journal_settings = graphene.Field(JournalSettingsType)

    @operator_required
    async def resolve_users(self, _info, *args, **kwargs):
        users = await User.get_objects(
            include_inactive=True,
        )
        objects = [UserType.instance_to_type(user) for user in users]
        return objects

    @administrator_required
    async def resolve_journal_settings(self, _info, **kwargs):
        settings = await JournalSettings.query.gino.all()
        settings_list = list()
        for row in settings:
            settings_list = JournalSettingsType(**row.__values__)
        return settings_list

    @operator_required
    async def resolve_count(
        self,
        _info,
        event_type=None,
        start_date=None,
        end_date=None,
        user=None,
        read_by=None,
        entity_type=None,
        entity=None,
        **kwargs
    ):
        filters = build_filters(
            event_type, start_date, end_date, user, read_by, entity_type, entity
        )
        query = (
            Event.outerjoin(EventReadByUser)
            .outerjoin(User)
            .outerjoin(Entity)
            .select()
            .where(and_(*filters))
            .where(Entity.entity_type != None)  # noqa: E711
        )
        event_count = (
            await db.select([db.func.count()]).select_from(query.alias()).gino.scalar()
        )
        return event_count

    @operator_required
    async def resolve_entity_types(
        self,
        _info,
        event_type=None,
        start_date=None,
        end_date=None,
        user=None,
        read_by=None,
        entity_type=None,
        **kwargs
    ):
        filters = build_filters(
            event_type, start_date, end_date, user, read_by, entity_type
        )

        query = (
            Event.outerjoin(EventReadByUser)
            .outerjoin(User)
            .outerjoin(Entity)
            .select()
            .where(and_(*filters))
            .where(Entity.entity_type != None)  # noqa: E711
        )

        query = (
            db.select([text("anon_1.entity_type")])
            .select_from(query.alias())
            .group_by(text("anon_1.entity_type"))
        )

        entity_types = await query.gino.all()
        return [entity[0] for entity in entity_types]

    @operator_required
    async def resolve_events(
        self,
        _info,
        limit,
        offset,
        event_type=None,
        start_date=None,
        end_date=None,
        user=None,
        read_by=None,
        entity_type=None,
        ordering=None,
        entity=None,
        **kwargs
    ):
        filters = build_filters(
            event_type, start_date, end_date, user, read_by, entity_type, entity
        )

        query = (
            Event.outerjoin(EventReadByUser).outerjoin(User).outerjoin(Entity).select()
        )

        events = (
            await query.where(and_(*filters))
            .order_by(desc(Event.created))
            .limit(limit)
            .offset(offset)
            .gino.load(
                Event.distinct(Event.id).load(
                    add_read_by=User.distinct(User.id), add_entity=Entity
                )
            )
            .all()
        )
        event_type_list = [
            EventType(
                read_by=[UserType(**user.__values__) for user in event.read_by],
                entity=[EntityType(**entity.__values__) for entity in event.entity],
                **event.__values__
            )
            for event in events
        ]

        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)

            if ordering == "user":

                def sort_lam(event):
                    return event.user if event.user else DEFAULT_NAME

            # elif ordering == 'message':
            #     def sort_lam(event): return event.message if event.message else DEFAULT_NAME
            elif ordering == "created":

                def sort_lam(event):
                    return event.created if event.created else "2000-01-01T00:00:01Z"

            else:
                raise SimpleError(_local_("The sort parameter is incorrect."))
            event_type_list = sorted(event_type_list, key=sort_lam, reverse=reverse)

        return event_type_list

    @operator_required
    async def resolve_event(self, _info, id, **kwargs):
        query = (
            Event.outerjoin(EventReadByUser)
            .outerjoin(User)
            .outerjoin(Entity)
            .select()
            .where(Event.id == id)
        )

        event = await query.gino.load(
            Event.distinct(Event.id).load(
                add_read_by=User.distinct(User.id), add_entity=Entity
            )
        ).first()

        if not event:
            raise GraphQLError(_local_("No such event."))

        event_type = EventType(
            read_by=[UserType(**user.__values__) for user in event.read_by],
            entity=[entity for entity in event.entity],
            **event.__values__
        )

        return event_type

    async def resolve_veil_events_count(
        self,
        _info,
        event_type=None,
        controller=None,
        **kwargs
    ):
        controllers = await ControllerFetcher.fetch_all()
        count = 0
        for controller_obj in controllers:
            if controller and (controller_obj.id != controller):
                continue
            veil_user = await controller_obj.get_veil_user
            for type_ in VeilEventTypeEnum:
                if event_type is type_.value:
                    event_type = type_.name
            veil_events = await controller_obj.veil_client.event().list(
                event_type=event_type, user=veil_user)
            count += veil_events.paginator_count
        return count

    @administrator_required
    async def resolve_veil_events(self, _info, limit, offset, controller=None,
                                  event_type=None,
                                  ordering: str = None, **kwargs):
        controllers = await ControllerFetcher.fetch_all()
        veil_events = list()
        for controller_obj in controllers:
            if controller and (controller_obj.id != controller):
                continue
            paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
            veil_user = await controller_obj.get_veil_user
            if not controller_obj.veil_client:
                return
            for type_ in VeilEventTypeEnum:
                if event_type is type_.value:
                    event_type = type_.name
            veil_response = await controller_obj.veil_client.event().list(
                paginator=paginator, user=veil_user, event_type=event_type
            )
            for data in veil_response.response:
                event = data.public_attrs
                # Добавляем id, так как в response он не присутствует в чистом виде
                event["id"] = event["api_object_id"]
                event["event_type"] = VeilEventTypeEnum[event["type"]]
                event["description"] = event["detail_message"]
                event["created"] = datetime.strptime("{}".format(event["created"]),
                                                     "%Y-%m-%dT%H:%M:%S.%fZ")
                veil_events.append(VeilEventType(**event))
        veil_events.sort(key=lambda events: events.created, reverse=True)
        return veil_events


class MarkEventsReadByMutation(graphene.Mutation):
    class Arguments:
        user = graphene.UUID(required=True)
        events = graphene.List(graphene.UUID)

    ok = graphene.Boolean()

    @operator_required
    async def mutate(self, _info, user, creator, events=None, **kwargs):
        await Event.mark_read_by(user, events)
        return MarkEventsReadByMutation(ok=True)


class UnmarkEventsReadByMutation(graphene.Mutation):
    class Arguments:
        user = graphene.UUID(required=True)
        events = graphene.List(graphene.UUID)

    ok = graphene.Boolean()

    @operator_required
    async def mutate(self, _info, user, creator, events=None, **kwargs):
        await Event.unmark_read_by(user, events)
        return UnmarkEventsReadByMutation(ok=True)


class EventExportMutation(graphene.Mutation):
    class Arguments:
        start = graphene.DateTime(
            description="Дата начала периода для экспорта журнала"
        )
        finish = graphene.DateTime(
            description="Дата окончания периода для экспорта журнала"
        )
        journal_path = ShortString(
            description="Адрес директории для экспорта журнала"
        )

    ok = graphene.Boolean()

    @operator_required
    async def mutate(self, _info, creator, start, finish, journal_path="/tmp/", **kwargs):
        name = await Event.event_export(start, finish, journal_path)
        entity = {"entity_type": "SECURITY", "entity_uuid": None}
        await system_logger.info(
            _local_("Journal is exported."), description=name, entity=entity, user=creator
        )
        return EventExportMutation(ok=True)


class ChangeJournalSettingsMutation(graphene.Mutation):
    class Arguments:
        dir_path = ShortString(description="Адрес директории для архивации журнала")
        period = ShortString(description="Период для архивации")
        by_count = graphene.Boolean(description="Принцип архивации")
        count = graphene.Int(description="Количество записей для архивации")

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, creator, **kwargs):
        await JournalSettings.change_journal_settings(creator=creator, **kwargs)
        return ChangeJournalSettingsMutation(ok=True)


class EventMutations(graphene.ObjectType):
    markEventsReadBy = MarkEventsReadByMutation.Field()
    unmarkEventsReadBy = UnmarkEventsReadByMutation.Field()
    # removeAllEvents = RemoveAllEventsMutation.Field()
    eventExport = EventExportMutation.Field()
    changeJournalSettings = ChangeJournalSettingsMutation.Field()


event_schema = graphene.Schema(
    query=EventQuery, mutation=EventMutations, auto_camelcase=False
)
