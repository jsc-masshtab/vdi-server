from starlette.responses import JSONResponse
from starlette.graphql import GraphQLApp # as starlette_GraphQLApp
import graphene

import sys

from .app import app

from .db import db

from .settings import settings

from .pool import Pool

from asyncpg.connection import Connection

import json

from graphql.backend import get_default_backend
from graphql.execution import ExecutionResult

# class GraphQLApp(starlette_GraphQLApp):
#
#     async def handle_graphql(self, request):
#         resp = await super().handle_graphql(request)
#         # a sad line
#         dic = json.loads(resp.body)
#         if dic['errors']:
#             del dic['data']
#             return JSONResponse(dic)
#         return JSONResponse(dic['data'])

import graphene

class PoolState(graphene.Enum):
    RUNNING = 1
    STOPPED = 0

class PoolType(graphene.ObjectType):
    id = graphene.Int()
    template_id = graphene.String()
    name = graphene.String()
    state = graphene.Field(PoolState)


class AddPool(graphene.Mutation):
    class Arguments:
        template_id = graphene.String()
        name = graphene.String()
        autostart = graphene.Boolean(default_value=True)

    id = graphene.Int()

    @db.transaction()
    async def mutate(self, info, args, conn: Connection):
        # insert vm
        vm_query = '''
        INSERT INTO templatevm (id) VALUES ($1) ON CONFLICT (id) DO NOTHING;
        ''', args['vm_id']
        await conn.fetch(*vm_query)
        # insert pool
        pool_query = '''INSERT INTO pool (template_id, name) VALUES ($1, $2) RETURNING id
        ''', args['template_id'], args['name']
        [res] = await conn.fetch(*pool_query)
        pool = {
            'id': res['id'],
            'name': args['name'],
            'template_id': args['template_id'],
        }
        if args['autostart']:
            ins = Pool(**pool)
            Pool.instances[pool['id']] = ins
            await ins.initial_tasks()
        return AddPool(id=pool['id'])




class PoolMutations(graphene.ObjectType):
    add = AddPool.Field()


def get_selections(info):
    return [
        f.name.value
        for f in info.field_asts[0].selection_set.selections
    ]


class PoolQuery(graphene.ObjectType):
    list = graphene.List(PoolType)
    instance = graphene.Field(PoolType, id=graphene.Int())

    @db.connect()
    async def resolve_instance(self, info, id, conn: Connection):
        fields = get_selections(info)
        state = None
        if 'state' in fields:
            fields.remove('state')
            if id in Pool.instances:
                state = PoolState.RUNNING
            else:
                state = PoolState.STOPPED
        qu = f'''
        SELECT ({', '.join(fields)}) FROM pool
        WHERE id = '{id}'
        '''
        [pool] = await conn.fetch(qu)
        dic = {
            f: pool[f] for f in fields
        }
        if state:
            dic['state'] = state
        return PoolType(**dic)

    @db.connect()
    async def resolve_list(self, info, conn: Connection):
        fields = get_selections(info)
        qu = f'''
        SELECT ({', '.join(fields)}) FROM pool'''
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

app.add_route('/', GraphQLApp(schema, executor_class=AsyncioExecutor))




