import graphene

from event.models import Event
from sqlalchemy import desc


class EventType(graphene.ObjectType):
    id = graphene.String()
    event_type = graphene.Int()
    message = graphene.String()
    created = graphene.DateTime()
    user = graphene.String()


class EventQuery(graphene.ObjectType):
    events = graphene.List(
        lambda: EventType,
        first=graphene.Int(),
        skip=graphene.Int()
    )

    async def resolve_events(self, _info, first=None, skip=None):
        events = await Event.query.order_by(desc(Event.created)).gino.all()

        # skip first n items
        if skip:
            events = events[skip:]

        # returns first n items
        if first:
            events = events[:first]

        objects = [
            EventType(**event.__values__)
            for event in events
        ]
        return objects


event_schema = graphene.Schema(query=EventQuery,
                               auto_camelcase=False)
