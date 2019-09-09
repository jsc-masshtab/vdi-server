import json
import urllib

import graphene
from vdi.tasks.client import HttpClient

from vdi.hashers import make_password, check_username
from vdi.settings import settings
from vdi.db import db
from vdi.errors import SimpleError
from vdi.constants import NotSet
from .util import get_selections

from vdi.auth import VDIUser, fetch_token
from vdi.application import Request

class UserType(graphene.ObjectType):
    username = graphene.String()
    email = graphene.String(default_value=NotSet)
    date_joined = graphene.DateTime(default_value=NotSet)

    sql_data = None

    async def get_sql_data(self):
        fields = [f for f in self._meta.fields]
        qu = (
            f'select {", ".join(fields)} from public.user'
            ' where username = $1', self.username
        )
        async with db.connect() as conn:
            users = await conn.fetch(*qu)
            [data] = users
            return data

    async  def resolve_username(self, info):
        if not self.sql_data:
            self.sql_data = await self.get_sql_data()
        return self.sql_data['username']

    async def resolve_email(self, info):
        if self.email is not NotSet:
            return self.email
        if not self.sql_data:
            self.sql_data = await self.get_sql_data()
        return self.sql_data['email']

    async def resolve_date_joined(self, info):
        if self.date_joined is not NotSet:
            return self.date_joined
        if not self.sql_data:
            self.sql_data = await self.get_sql_data()
        return self.sql_data['date_joined']



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
            qu = (
                "INSERT INTO public.user (username, password, email) VALUES ($1, $2, $3)",
                username, password, email
            )
            await conn.execute(*qu)
        return {
            'ok': True
        }


# class GetToken(graphene.Mutation):
#
#     class Arguments:
#         username = graphene.String()
#         password = graphene.String()
#
#     token = graphene.String()
#
#     async def mutate(self):


class ChangePassword(graphene.Mutation):
    class Arguments:
        username = graphene.String()
        new_password = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()

    async def mutate(self, info, username, new_password, password=None):
        user = await VDIUser.get()
        if not user or 'admin' not in user.roles:
            if not password:
                raise SimpleError('Пароль обязателен')
            valid = await check_username(username, password)
            if not valid:
                raise SimpleError("Неверные учётные данные")
        async with db.connect() as conn:
            encoded = make_password(new_password)
            qu = "update public.user set password = $1 where username = $2", encoded, username
            await conn.execute(*qu)
        return ChangePassword(ok=True)


class AuthInfo(graphene.ObjectType):
    token = graphene.String()


class UserQueries:
    users = graphene.List(UserType)
    #TMP
    check_user = graphene.Field(graphene.Boolean, username=graphene.String(), password=graphene.String())
    auth = graphene.Field(AuthInfo, username=graphene.String(), password=graphene.String())

    async def resolve_auth(self, info, **kwargs):
        data = await fetch_token(**kwargs)
        token = data['access_token']
        return AuthInfo(token=token)

    async def resolve_check_user(self, info, username, password):
        return await check_username(username, password)

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


