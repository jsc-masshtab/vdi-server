

import graphene

from asyncpg.connection import Connection

from ..db import db
from ..tasks import vm

from .util import get_selections
from vdi.context_utils import enter_context


class UserType(graphene.ObjectType):
    username = graphene.String()
    password = graphene.String()
    email = graphene.String()


class CreateUser(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        username = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()

    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info, username, password):
        qu = '''
            INSERT INTO public.user (username, password) VALUES ($1, $2)
            ''', username, password
        await conn.execute(*qu)
        return {
            'ok': True
        }


class ListUsers:
    users = graphene.List(UserType)

    @enter_context(lambda: db.connect())
    async def resolve_users(conn: Connection, self, info):
        fields = get_selections(info)
        qu = f"SELECT {', '.join(fields)} FROM public.user"
        users = await conn.fetch(qu)
        li = []
        for rec in users:
            user = dict(zip(fields, rec))
            li.append(UserType(**user))
        return li
