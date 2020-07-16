# -*- coding: utf-8 -*-
import graphene
from graphql import GraphQLError
from sqlalchemy import desc, and_, text

from database import db
from common.veil_decorators import administrator_required
from common.utils import extract_ordering_data
from common.veil_errors import SimpleError
from journal.event.models import Event, EventReadByUser, EventEntity
from auth.models import Entity
from auth.user_schema import User, UserType

from settings import DEFAULT_NAME

from languages import lang_init
from journal.journal import Log


_ = lang_init()


def build_filters(event_type, start_date, end_date, user, read_by, entity_type):
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

    return filters


class EntityType(graphene.ObjectType):
    id = graphene.UUID()
    entity_uuid = graphene.UUID()
    entity_type = graphene.String()


class EventType(graphene.ObjectType):
    id = graphene.UUID()
    event_type = graphene.Int()
    message = graphene.String()
    description = graphene.String()
    created = graphene.DateTime()
    user = graphene.String()
    read_by = graphene.List(UserType)
    entity = graphene.List(EntityType)
    entity_types = graphene.List(graphene.String)


class EventQuery(graphene.ObjectType):
    count = graphene.Int(
        event_type=graphene.Int(),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        user=graphene.String(),
        read_by=graphene.UUID(),
        entity_type=graphene.String())

    events = graphene.List(
        lambda: EventType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        event_type=graphene.Int(),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        user=graphene.String(),
        read_by=graphene.UUID(),
        entity=graphene.UUID(),
        entity_type=graphene.String(),
        ordering=graphene.String())

    event = graphene.Field(
        lambda: EventType,
        id=graphene.UUID())

    entity_types = graphene.List(
        graphene.String,
        event_type=graphene.Int(),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        user=graphene.String(),
        read_by=graphene.UUID(),
        entity_type=graphene.String()
    )

    @administrator_required
    async def resolve_count(self, _info, event_type=None, start_date=None,
                            end_date=None, user=None, read_by=None, entity_type=None, **kwargs):
        filters = build_filters(event_type, start_date, end_date, user, read_by, entity_type)
        query = Event.outerjoin(EventReadByUser).outerjoin(User).outerjoin(
            EventEntity).outerjoin(Entity).select().where(and_(*filters)).where(Entity.entity_type != None)  # noqa
        event_count = await db.select([db.func.count()]).select_from(query.alias()).gino.scalar()
        return event_count

    @administrator_required
    async def resolve_entity_types(self, _info, event_type=None, start_date=None,
                                   end_date=None, user=None, read_by=None, entity_type=None, **kwargs):
        # TODO: refactor me
        filters = build_filters(event_type, start_date, end_date, user, read_by, entity_type)

        query = Event.outerjoin(EventReadByUser).outerjoin(User).outerjoin(
            EventEntity).outerjoin(Entity).select().where(
            and_(*filters)
        ).where(Entity.entity_type != None)  # noqa

        query = db.select([text('anon_1.entity_type')]).select_from(query.alias()).group_by(text('anon_1.entity_type'))

        entity_types = await query.gino.all()
        return [entity[0] for entity in entity_types]

    @administrator_required
    async def resolve_events(self, _info, limit, offset, event_type=None,
                             start_date=None, end_date=None, user=None,
                             read_by=None, entity_type=None, ordering=None, **kwargs):
        filters = build_filters(event_type, start_date, end_date, user, read_by, entity_type)

        query = Event.outerjoin(EventReadByUser).outerjoin(User).outerjoin(
            EventEntity).outerjoin(Entity).select()

        events = await query.where(
            and_(*filters)
        ).order_by(desc(Event.created)).limit(limit).offset(offset).gino.load(
            Event.distinct(Event.id).load(add_read_by=User.distinct(User.id),
                                          add_entity=Entity)
        ).all()

        event_type_list = [
            EventType(
                read_by=[UserType(**user.__values__) for user in event.read_by],
                entity=[EntityType(**entity.__values__) for entity in event.entity],
                **event.__values__)
            for event in events
        ]

        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)

            if ordering == 'user':
                def sort_lam(event): return event.user if event.user else DEFAULT_NAME
            # elif ordering == 'message':
            #     def sort_lam(event): return event.message if event.message else DEFAULT_NAME
            elif ordering == 'created':
                def sort_lam(event): return event.created if event.created else "2000-01-01T00:00:01Z"
            else:
                raise SimpleError(_('The sort parameter is incorrect'))
            event_type_list = sorted(event_type_list, key=sort_lam, reverse=reverse)

        return event_type_list

    @administrator_required
    async def resolve_event(self, _info, id, **kwargs):
        query = Event.outerjoin(EventReadByUser).outerjoin(User).outerjoin(
            EventEntity).outerjoin(Entity).select().where(Event.id == id)

        event = await query.gino.load(
            Event.distinct(Event.id).load(add_read_by=User.distinct(User.id), add_entity=Entity)
        ).first()

        if not event:
            raise GraphQLError(_('No such event.'))

        event_type = EventType(
            read_by=[UserType(**user.__values__) for user in event.read_by],
            entity=[entity for entity in event.entity],
            **event.__values__)

        return event_type


class MarkEventsReadByMutation(graphene.Mutation):
    class Arguments:
        user = graphene.UUID(required=True)
        events = graphene.List(graphene.UUID)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, user, events=None, **kwargs):
        await Event.mark_read_by(user, events)
        return RemoveAllEventsMutation(ok=True)


class UnmarkEventsReadByMutation(graphene.Mutation):
    class Arguments:
        user = graphene.UUID(required=True)
        events = graphene.List(graphene.UUID)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, user, events=None, **kwargs):
        await Event.unmark_read_by(user, events)
        return UnmarkEventsReadByMutation(ok=True)


class RemoveAllEventsMutation(graphene.Mutation):
    class Arguments:
        ok = graphene.Boolean()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, **kwargs):
        await Event.delete.gino.status()
        await Log.info(_("Journal is clear."))
        return RemoveAllEventsMutation(ok=True)


class EventMutations(graphene.ObjectType):
    markEventsReadBy = MarkEventsReadByMutation.Field()
    unmarkEventsReadBy = UnmarkEventsReadByMutation.Field()
    removeAllEvents = RemoveAllEventsMutation.Field()


event_schema = graphene.Schema(query=EventQuery,
                               mutation=EventMutations,
                               auto_camelcase=False)
