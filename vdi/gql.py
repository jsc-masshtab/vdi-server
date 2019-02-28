import asyncio
from starlette.responses import JSONResponse
from starlette.graphql import GraphQLApp # as starlette_GraphQLApp
import graphene

import sys
from cached_property import cached_property as cached


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

class RunningState(graphene.Enum):
    RUNNING = 1
    STOPPED = 0

class PoolType(graphene.ObjectType):
    id = graphene.Int()
    template_id = graphene.String()
    name = graphene.String()
    state = graphene.Field(lambda: PoolState)

    @cached
    def pool_id(self):
        raise NotImplementedError

    def resolve_state(self, info):
        if self.pool_id not in Pool.instances:
            return PoolState(running=False)
        state = PoolState(running=True)
        state.pool = Pool.instances[self.pool_id]
        return state


class VmType(graphene.ObjectType):
    name = graphene.String()
    id = graphene.String()
    info = graphene.String()


class PoolState(graphene.ObjectType):
    running = graphene.Field(RunningState)
    available = graphene.List(VmType)
    pending = graphene.Int() # will change
                             # will be the ids of vms

    @cached
    def pool(self):
        raise NotImplementedError

    async def resolve_pending(self, info):
        return self.pool.pending

    async def resolve_available(self, info):
        qu = self.pool.queue._queue
        ret = []
        for vm in qu:
            info = json.dumps(vm)
            ret.append(VmType(id=vm['id'], info=info))
        return ret


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
        INSERT INTO vm (id) VALUES ($1) ON CONFLICT (id) DO NOTHING;
        ''', args['template_id']
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
            ins.schedule_tasks()
        return AddPool(id=pool['id'])


class LaunchPool(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    state = graphene.Field(PoolState)

    @db.connect()
    async def mutate(self, info, id, conn: Connection):
        if id in Pool.instances:
            pool = Pool.instances[id]
        else:
            qu = f'''
            SELECT template_id, name FROM pool
            WHERE id = '{id}'
            '''
            [dic] = await conn.fetch(qu)
            pool = Pool(**dic)
            Pool.instances[id] = pool
            task = pool.schedule_tasks()
            asyncio.create_task(task)
        state = PoolState(running=True)
        state.pool = pool
        return LaunchPool(state=state)


# TODO create template vm


class PoolMutations(graphene.ObjectType):
    add = AddPool.Field()
    launch = LaunchPool.Field()

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




