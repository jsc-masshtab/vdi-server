import graphene
from graphql import GraphQLError
from sqlalchemy import desc, and_

from common.veil_decorators import superuser_required

from event.models import Event, EventReadByUser

from database import db
from event.models import Event, EventReadByUser
from user.schema import User, UserType


class EventType(graphene.ObjectType):
    id = graphene.UUID()
    event_type = graphene.Int()
    message = graphene.String()
    description = graphene.String()
    created = graphene.DateTime()
    user = graphene.String()
    read_by = graphene.List(UserType)


class EventQuery(graphene.ObjectType):
    count = graphene.Int()
    events = graphene.List(
        lambda: EventType,
        limit=graphene.Int(),
        offset=graphene.Int(),
        event_type=graphene.Int(),
        start_date=graphene.DateTime(),
        end_date=graphene.DateTime(),
        user=graphene.String(),
        read_by=graphene.UUID())
    event = graphene.Field(
        lambda: EventType,
        id=graphene.UUID())

    async def resolve_count(self, _info):
        event_count = db.func.count(Event.id).gino.scalar()
        return event_count

    @superuser_required
    async def resolve_events(self, _info, limit=100, offset=0, event_type=None,
                             start_date=None, end_date=None, user=None, read_by=None):
        filters = []

        if event_type:
            filters.append((Event.event_type == event_type))
        if start_date:
            filters.append((Event.created >= start_date))
        if end_date:
            filters.append((Event.created <= end_date))
        if user:
            filters.append((Event.user == user))

        query = Event.outerjoin(EventReadByUser).outerjoin(User).select()

        events = await query.where(
            and_(*filters)
        ).order_by(desc(Event.created)).limit(limit).offset(offset).gino.load(
            Event.distinct(Event.id).load(add_read_by=User.distinct(User.id))
        ).all()

        event_type_list = [
            EventType(
                read_by=[UserType(**user.__values__) for user in event.read_by],
                **event.__values__)
            for event in events
        ]
        return event_type_list

    @superuser_required
    async def resolve_event(self, _info, id):
        query = Event.outerjoin(EventReadByUser).outerjoin(User).select()
        event = await query.where(Event.id == id).gino.load(
            Event.distinct(Event.id).load(add_read_by=User.distinct(User.id))
        ).first()

        if not event:
            raise GraphQLError('No such event.')

        event_type = EventType(
            read_by=[UserType(**user.__values__) for user in event.read_by],
            **event.__values__)

        return event_type


class MarkEventsReadByMutation(graphene.Mutation):
    class Arguments:
        user = graphene.UUID(required=True)
        events = graphene.List(graphene.UUID)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, user, events=None):
        await Event.mark_read_by(user, events)
        return RemoveAllEventsMutation(ok=True)


class UnmarkEventsReadByMutation(graphene.Mutation):
    class Arguments:
        user = graphene.UUID(required=True)
        events = graphene.List(graphene.UUID)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, user, events=None):
        await Event.unmark_read_by(user, events)
        return UnmarkEventsReadByMutation(ok=True)


class RemoveAllEventsMutation(graphene.Mutation):
    class Arguments:
        ok = graphene.Boolean()

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info):
        await Event.delete.gino.status()
        await Event.create_info("Журнал очищен")
        return RemoveAllEventsMutation(ok=True)


class EventMutations(graphene.ObjectType):
    markEventsReadBy = MarkEventsReadByMutation.Field()
    unmarkEventsReadBy = UnmarkEventsReadByMutation.Field()
    removeAllEvents = RemoveAllEventsMutation.Field()


event_schema = graphene.Schema(query=EventQuery,
                               mutation=EventMutations,
                               auto_camelcase=False)
