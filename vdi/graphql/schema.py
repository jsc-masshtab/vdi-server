import graphene
from asyncpg.connection import Connection
from starlette.graphql import GraphQLApp  # as starlette_GraphQLApp

from .pool import PoolType, LaunchPool, AddPool
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

class PoolQuery(ListUsers, graphene.ObjectType):
    pools = graphene.List(PoolType)
    pool = graphene.Field(PoolType, id=graphene.Int())

    @db.connect()
    async def resolve_pool(self, info, id, conn: Connection):
        fields = [
            f for f in get_selections(info)
            if f in PoolType.sql_fields
        ]
        qu = f'''
        SELECT {', '.join(fields)} FROM pool
        WHERE id = '{id}'
        '''
        [pool] = await conn.fetch(qu)
        dic = {
            f: pool[f] for f in fields
        }
        ret = PoolType(**dic)
        ret.pool_id = id
        return ret

    @db.connect()
    async def resolve_pools(self, info, conn: Connection):
        fields = get_selections(info)
        qu = f"SELECT {', '.join(fields)} FROM pool"
        pools = await conn.fetch(qu)
        items = []
        for p in pools:
            p = {
                f: p[f] for f in fields
            }
            items.append(PoolType(**p))
        return items



from graphql.execution.executors.asyncio import AsyncioExecutor

schema = graphene.Schema(query=PoolQuery, mutation=PoolMutations, auto_camelcase=False)

app.add_route('/admin', GraphQLApp(schema, executor_class=AsyncioExecutor))

