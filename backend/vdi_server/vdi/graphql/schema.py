import graphene
from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.graphql import graphql

from .pool import AddPool, PoolMixin, RemovePool, WakePool, EntitleUsersToPool, RemoveUserEntitlementsFromPool
from .resources import AddController, RemoveController, Resources
from .users import CreateUser, ListUsers
from .vm import PoolWizardMixin


class PoolMutations(graphene.ObjectType):
    removePool = RemovePool.Field()
    addPool = AddPool.Field()
    wakePool = WakePool.Field()
    createUser = CreateUser.Field()

    addController = AddController.Field()
    removeController = RemoveController.Field()

    entitleUsersToPool = EntitleUsersToPool.Field()
    removeUserEntitlementsFromPool = RemoveUserEntitlementsFromPool.Field()

class PoolQuery(ListUsers, Resources, PoolMixin, PoolWizardMixin, graphene.ObjectType):
    pass


schema = graphene.Schema(query=PoolQuery, mutation=PoolMutations, auto_camelcase=False)



class ExecError(Exception):
    pass


async def exec(query, variables=None):
    r = await graphql(schema, query, variables=variables, executor=AsyncioExecutor(), return_promise=True)
    if r.errors:
        raise ExecError(repr(r.errors))
    return r.data