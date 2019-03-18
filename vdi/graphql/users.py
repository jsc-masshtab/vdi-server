

import graphene

from asyncpg.connection import Connection

from ..db import db
from ..tasks import vm

from .util import get_selections


class UserType(graphene.ObjectType):
    username = graphene.String()
    password = graphene.String()


class CreateUser(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        username = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()

    @db.connect()
    async def mutate(self, info, username, password, conn: Connection):
        qu = '''
            INSERT INTO public.user (username, password) VALUES ($1, $2)
            ''', username, password
        await conn.execute(*qu)
        return {
            'ok': True
        }


class ListUsers:
    users = graphene.List(UserType)

    @db.connect()
    async def resolve_users(self, info, conn: Connection):
        fields = get_selections(info)
        qu = f"SELECT {', '.join(fields)} FROM public.user"
        users = await conn.fetch(qu)
        li = []
        for rec in users:
            user = dict(zip(fields, rec))
            li.append(UserType(**user))
        return li
