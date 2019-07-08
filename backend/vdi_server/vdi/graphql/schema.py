import graphene
from asyncpg.connection import Connection
from graphql.graphql import graphql
from graphql.execution.executors.asyncio import AsyncioExecutor


from .pool import PoolType, AddPool, PoolMixin, RemovePool, WakePool
from .vm import TemplateMixin, PoolWizardMixin
from .users import CreateUser, ListUsers
from .resources import Resources, AddController, RemoveController


class PoolMutations(graphene.ObjectType):
    removePool = RemovePool.Field()
    addPool = AddPool.Field()
    wakePool = WakePool.Field()
    createUser = CreateUser.Field()

    addController = AddController.Field()
    removeController = RemoveController.Field()


class PoolQuery(ListUsers, Resources, PoolMixin, TemplateMixin, PoolWizardMixin, graphene.ObjectType):
    pass


schema = graphene.Schema(query=PoolQuery, mutation=PoolMutations, auto_camelcase=False)



class ExecError(Exception):
    pass


async def exec(query, variables=None):
    r = await graphql(schema, query, variables=variables, executor=AsyncioExecutor(), return_promise=True)
    if r.errors:
        raise ExecError(repr(r.errors))
    return r.data