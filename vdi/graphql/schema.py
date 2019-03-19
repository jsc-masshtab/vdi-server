import graphene
from asyncpg.connection import Connection
from starlette.graphql import GraphQLApp  # as starlette_GraphQLApp

from .pool import PoolType, LaunchPool, AddPool, PoolMixin
from .util import get_selections
from .vm import CreateTemplate, AddTemplate
from .users import CreateUser, ListUsers

from ..app import app
from ..db import db


class PoolMutations(graphene.ObjectType):
    addPool = AddPool.Field()
    launchPool = LaunchPool.Field()
    createTemplate = CreateTemplate.Field()
    addTemplate = AddTemplate.Field()
    createUser = CreateUser.Field()

class PoolQuery(ListUsers, PoolMixin, graphene.ObjectType):
    1



from graphql.execution.executors.asyncio import AsyncioExecutor

schema = graphene.Schema(query=PoolQuery, mutation=PoolMutations, auto_camelcase=False)

app.add_route('/admin', GraphQLApp(schema, executor_class=AsyncioExecutor))

