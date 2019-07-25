

import graphene

from asyncpg.connection import Connection

from ..db import db
from ..tasks import vm

from .util import get_selections


class UserType(graphene.ObjectType):
    username = graphene.String()
    password = graphene.String()
    email = graphene.String()

    async def resolve_email(self, info):
        if self.email:
            return self.email
        qu = 'select email from public.user where username = $1', self.username
        async with db.connect() as conn:
            [(email,)] = await conn.fetch(*qu)
            return email


class CreateUser(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        username = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()

    async def mutate(self, info, username, password):
        async with db.connect() as conn:
            qu = '''
                INSERT INTO public.user (username, password) VALUES ($1, $2)
                ''', username, password
            await conn.execute(*qu)
        return {
            'ok': True
        }


class ListUsers:
    users = graphene.List(UserType)

    async def resolve_users(self, info):
        fields = get_selections(info)
        async with db.connect() as conn:
            qu = f"SELECT {', '.join(fields)} FROM public.user"
            users = await conn.fetch(qu)
        li = []
        for rec in users:
            user = dict(zip(fields, rec))
            li.append(UserType(**user))
        return li
