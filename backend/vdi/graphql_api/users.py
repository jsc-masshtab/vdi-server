import json
import urllib

import graphene
from vdi.tasks.client import HttpClient

from vdi.hashers import make_password, check_username
from vdi.settings import settings
from db.db import db
from vdi.errors import SimpleError
from vdi.constants import NotSet
from .util import get_selections

from vdi.auth import VDIUser, fetch_token
from vdi.application import Request

#from vdi.graphql_api.pool import PoolType

class UserType(graphene.ObjectType):
    username = graphene.String()
    email = graphene.String(default_value=NotSet)
    date_joined = graphene.DateTime(default_value=NotSet)
    #pools = graphene.List(PoolType)

    sql_data = None

    # unused? marked for removal
    async def get_sql_data(self):
        fields = [f for f in self._meta.fields]

        sql_request_fields = ", ".join(fields)
        qu = """SELECT $1 from public.user where username = $2""", sql_request_fields, self.username
        async with db.connect() as conn:
            users = await conn.fetch(*qu)
            [data] = users
            return data

    async  def resolve_username(self, _info):
        return self.username

    async def resolve_email(self, _info):
        if self.email is not NotSet:
            return self.email

        async with db.connect() as conn:
            sql_request = """SELECT email from public.user where username = $1""", self.username
            email_data = await conn.fetch(*sql_request)
            if email_data:
                [(email,)] = email_data
                return email
            else:
                return None

    async def resolve_date_joined(self, _info):
        if self.date_joined is not NotSet:
            return self.date_joined

        async with db.connect() as conn:
            sql_request = """SELECT date_joined from public.user where username = $1""", self.username
            date_joined_data = await conn.fetch(*sql_request)
            if date_joined_data:
                [(date_joined,)] = date_joined_data
                return date_joined
            else:
                return None

    # async def resolve_pools(self, _info):
    #     async with db.connect() as conn:
    #         sql_request = """SELECT pool_id FROM pools_users WHERE username = $1""", self.username
    #         pool_data = await conn.fetch(*sql_request)
    #
    #         pools_list = []
    #         return pools_list

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
    users = graphene.List(UserType, ordering=graphene.String(), reversed_order=graphene.Boolean())
    #TMP
    check_user = graphene.Field(graphene.Boolean, username=graphene.String(), password=graphene.String())
    auth = graphene.Field(AuthInfo, username=graphene.String(), password=graphene.String())

    async def resolve_auth(self, info, **kwargs):
        data = await fetch_token(**kwargs)
        token = data['access_token']
        return AuthInfo(token=token)

    async def resolve_check_user(self, info, username, password):
        return await check_username(username, password)

    async def resolve_users(self, info, ordering=None, reversed_order=None):
        fields = get_selections(info)

        if ordering:
            # is reversed
            sort_order = 'DESC' if reversed_order else 'ASC'
            # ordering
            qu = "SELECT {} FROM public.user ORDER BY {} {}".format(', '.join(fields), ordering, sort_order)
        else:
            qu = "SELECT {} FROM public.user".format(', '.join(fields))

        async with db.connect() as conn:
            users = await conn.fetch(qu)
        li = []
        for rec in users:
            print('fields', fields)
            print('rec', rec)
            user = dict(zip(fields, rec))
            li.append(UserType(**user))
        return li


