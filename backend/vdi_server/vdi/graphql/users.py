
import graphene

from vdi.app.hashers import make_password, check_password
from vdi.db import db
from .util import get_selections


def check_username(username, raw_password):
    encoded = make_password(raw_password)

    async def setter(raw_password):
        async with db.connect() as conn:
            qu = "update table public.user set password = $1 where username = $2", encoded, username
            await conn.execute(*qu)

    return check_password(raw_password, encoded, setter)

from typing import List
from classy_async import cached


class UserType(graphene.ObjectType):
    username = graphene.String()
    email = graphene.String()
    date_joined = graphene.DateTime()

    @cached
    async def get_sql_data(self):
        fields = [f for f in self._meta.fields if f != 'username']
        qu = f'select {fields.join(", ")} from public.user',
        async with db.connect() as conn:
            await conn.fetch(*qu)

    async def resolve_email(self, info):
        if self.email:
            return self.email
        sql_data = await self.get_sql_data()
        return sql_data['email']

    async def resolve_date_joined(self, info):
        if self.date_joined:
            return self.date_joined
        sql_data = await self.get_sql_data()
        return sql_data['date_joined']



class CreateUser(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        username = graphene.String()
        email = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()

    async def mutate(self, info, username, password, email=None):
        password = make_password(password)
        async with db.connect() as conn:
            qu = '''
                INSERT INTO public.user (username, password, email) VALUES ($1, $2, $3)
                ''', username, password, email
            await conn.execute(*qu)
        return {
            'ok': True
        }


class ListUsers:
    users = graphene.List(UserType)
    #TMP
    check_user = graphene.Field(graphene.Boolean, username=graphene.String(), password=graphene.String())

    async def resolve_check_user(self, info, username, password):
        return check_username(username, password)

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


