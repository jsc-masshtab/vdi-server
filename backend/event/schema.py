import graphene

from event.models import Event
from sqlalchemy import desc


class EventType(graphene.ObjectType):
    id = graphene.String()
    event_type = graphene.Int()
    message = graphene.String()
    description = graphene.String()
    created = graphene.DateTime()
    user = graphene.String()


class EventQuery(graphene.ObjectType):
    events = graphene.List(
        lambda: EventType,
        limit=graphene.Int(),
        offset=graphene.Int()
    )

    async def resolve_events(self, _info, limit=100, offset=0):
        events = await Event.query.order_by(desc(Event.created)).limit(limit).offset(offset).gino.all()

        objects = [
            EventType(**event.__values__)
            for event in events
        ]
        return objects


event_schema = graphene.Schema(query=EventQuery,
                               auto_camelcase=False)
