import graphene
from asyncpg.connection import Connection
from starlette.graphql import GraphQLApp  # as starlette_GraphQLApp
from graphql.execution.executors.asyncio import AsyncioExecutor


from .pool import PoolType, LaunchPool, AddPool, PoolMixin, RemovePool
from .util import get_selections
from .vm import CreateTemplate, AddTemplate, DropTemplate, TemplateMixin
from .users import CreateUser, ListUsers

from ..app import app
from ..db import db


class PoolMutations(graphene.ObjectType):
    removePool = RemovePool.Field()
    addPool = AddPool.Field()
    launchPool = LaunchPool.Field()
    createTemplate = CreateTemplate.Field()
    addTemplate = AddTemplate.Field()
    dropTemplate = DropTemplate.Field()
    createUser = CreateUser.Field()

class PoolQuery(ListUsers, PoolMixin, TemplateMixin, graphene.ObjectType):
    pass





schema = graphene.Schema(query=PoolQuery, mutation=PoolMutations, auto_camelcase=False)

app.add_route('/admin', GraphQLApp(schema, executor_class=AsyncioExecutor))


from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.graphql import graphql


async def exec(query):
    r = await graphql(schema, query, executor=AsyncioExecutor(), return_promise=True)
    return r