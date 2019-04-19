import graphene
from asyncpg.connection import Connection
from graphql.graphql import graphql
from graphql.execution.executors.asyncio import AsyncioExecutor


from .pool import PoolType, AddPool, PoolMixin, RemovePool
from .vm import CreateTemplate, AddTemplate, DropTemplate, TemplateMixin
from .users import CreateUser, ListUsers


class PoolMutations(graphene.ObjectType):
    removePool = RemovePool.Field()
    addPool = AddPool.Field()
    createTemplate = CreateTemplate.Field()
    addTemplate = AddTemplate.Field()
    dropTemplate = DropTemplate.Field()
    createUser = CreateUser.Field()


class PoolQuery(ListUsers, PoolMixin, TemplateMixin, graphene.ObjectType):
    pass


schema = graphene.Schema(query=PoolQuery, mutation=PoolMutations, auto_camelcase=False)



class ExecError(Exception):
    pass


async def exec(query):
    r = await graphql(schema, query, executor=AsyncioExecutor(), return_promise=True)
    if r.errors:
        raise ExecError(repr(r.errors))
    return r.data