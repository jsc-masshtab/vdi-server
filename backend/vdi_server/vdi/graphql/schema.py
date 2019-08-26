import graphene
from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.graphql import graphql

from .pool import AddPool, AddStaticPool, PoolMixin, RemovePool, WakePool, AddPoolPermissions, \
    DropPoolPermissions, AddVmsToStaticPool, RemoveVmsFromStaticPool
from .resources import AddController, RemoveController, Resources, Subscription
from .users import CreateUser, UserQueries, ChangePassword
from .vm import PoolWizardMixin, AssignVmToUser, FreeVmFromUser, ListOfVmsQuery


class PoolMutations(graphene.ObjectType):
    removePool = RemovePool.Field()
    addPool = AddPool.Field()
    addStaticPool = AddStaticPool.Field()
    addVmsToStaticPool = AddVmsToStaticPool.Field()
    removeVmsFromStaticPool = RemoveVmsFromStaticPool.Field()
    wakePool = WakePool.Field()

    createUser = CreateUser.Field()
    changePassword = ChangePassword.Field()

    addController = AddController.Field()
    removeController = RemoveController.Field()

    entitleUsersToPool = AddPoolPermissions.Field()
    addPoolPermissions = AddPoolPermissions.Field()
    removeUserEntitlementsFromPool = DropPoolPermissions.Field()
    dropPoolPermissions = DropPoolPermissions.Field()

    assignVmToUser = AssignVmToUser.Field()
    freeVmFromUser = FreeVmFromUser.Field()


class PoolQuery(UserQueries, Resources, PoolMixin, PoolWizardMixin, graphene.ObjectType, ListOfVmsQuery):
    pass


schema = graphene.Schema(query=PoolQuery, mutation=PoolMutations,
                         subscription=Subscription, auto_camelcase=False)


class ExecError(Exception):
    pass


async def exec(query, variables=None):
    r = await graphql(schema, query, variables=variables, executor=AsyncioExecutor(), return_promise=True)
    if r.errors:
        raise ExecError(repr(r.errors))
    return r.data