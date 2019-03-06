import asyncio
from starlette.responses import JSONResponse
from starlette.graphql import GraphQLApp # as starlette_GraphQLApp
import graphene

import sys
from cached_property import cached_property as cached


from ..app import app
from ..db import db
from ..settings import settings
from ..pool import Pool
from ..tasks import vm

from asyncpg.connection import Connection

import json
import graphene

class RunningState(graphene.Enum):
    RUNNING = 1
    STOPPED = 0

class PoolType(graphene.ObjectType):
    id = graphene.Int()
    template_id = graphene.String(required=True)
    initial_size = graphene.Int()
    reserve_size = graphene.Int()
    name = graphene.String()
    state = graphene.Field(lambda: PoolState)

    sql_fields = ['id', 'template_id', 'initial_size', 'reserve_size', 'name']

    @cached
    def pool_id(self):
        raise NotImplementedError

    def resolve_state(self, info):
        if self.pool_id not in Pool.instances:
            return PoolState(running=False)
        state = PoolState(running=True)
        state.pool = Pool.instances[self.pool_id]
        return state

    @classmethod
    def get_defaults(cls):
        # this will be settable in the UI
        return {
            'initial_size': 2,
            'reserve_size': 2,
        }


class VmType(graphene.ObjectType):
    name = graphene.String()
    id = graphene.String()
    info = graphene.String()


class PoolState(graphene.ObjectType):
    running = graphene.Field(RunningState)
    available = graphene.List(VmType)
    pending = graphene.Int() # will change
                             # will be the ids of vms

    pool = None

    async def resolve_pending(self, info):
        if self.pool is None:
            return None
        return self.pool.pending

    async def resolve_available(self, info):
        if self.pool is None:
            return []
        qu = self.pool.queue._queue
        ret = []
        for vm in qu:
            info = json.dumps(vm)
            ret.append(VmType(id=vm['id'], info=info))
        return ret

# TODO dict of pending tasks

class AddPool(graphene.Mutation):
    class Arguments:
        template_id = graphene.String()
        name = graphene.String(required=True)
        autostart = graphene.Boolean(default_value=True)
        block = graphene.Boolean(default_value=False)

    id = graphene.Int()
    # TODO return PoolState

    @db.transaction()
    async def mutate(self, info, conn: Connection, template_id, name, autostart, block):
        params = dict(
            PoolType.get_defaults(),
            template_id=template_id, name=name, autostart=autostart
        )
        pool_query = '''
        INSERT INTO pool (template_id, name, initial_size, reserve_size)
        VALUES ($1, $2, $3, $4) RETURNING id
        ''', params['template_id'], params['name'], params['initial_size'], params['reserve_size']
        [res] = await conn.fetch(*pool_query)
        pool = {
            'id': res['id'],
            'name': name,
            'template_id': template_id,
            'initial_size': params['initial_size']
        }
        if autostart:
            ins = Pool(params=pool)
            Pool.instances[pool['id']] = ins
            add_domains = ins.add_domains()
            if block:
                await add_domains
            else:
                asyncio.create_task(add_domains)
        return AddPool(id=pool['id'])


class LaunchPool(graphene.Mutation):
    #
    # development only ?
    #
    class Arguments:
        id = graphene.Int()
        block = graphene.Boolean(default_value=False)

    state = graphene.Field(PoolState)

    @db.connect()
    async def mutate(self, info, id, block, conn: Connection):
        if id in Pool.instances:
            from graphql import GraphQLError
            raise GraphQLError('pool is launched')

        qu = f'''
        SELECT pool.id, template_id, name, initial_size, reserve_size, vm.id as "vm.id"
        FROM pool LEFT JOIN vm
        ON vm.pool_id = pool.id WHERE pool.id = $1 AND vm.state = 'queued'
        ''', id
        records = await conn.fetch(*qu)
        rec = records[0]
        dic = {
            'id': rec['id'],
            'template_id': rec['template_id'],
            'name': rec['name'],
            'initial_size': rec['initial_size'],
            'reserve_size': rec['reserve_size'],
        }
        pool = Pool(params=dic)
        Pool.instances[id] = pool
        vms = [
            {
                'id': rec['vm.id'] # TODO: what about vm info?
            }
            for rec in records
        ]
        for vm in vms:
            await pool.queue.put(vm)
            pool.queue.task_done()
        add_domains = pool.add_domains()
        if block:
            await add_domains
        else:
            asyncio.create_task(add_domains)
        state = PoolState(running=True)
        state.pool = pool
        return LaunchPool(state=state)


def get_selections(info):
    return [
        f.name.value
        for f in info.field_asts[0].selection_set.selections
    ]


class PoolQuery(graphene.ObjectType):
    pools = graphene.List(PoolType)
    pool = graphene.Field(PoolType, id=graphene.Int())

    @db.connect()
    async def resolve_instance(self, info, id, conn: Connection):
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


class CreateTemplate(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        image_name = graphene.String()

    id = graphene.String()

    @db.connect()
    async def mutate(self, info, image_name, conn: Connection):
        domain = await vm.SetupDomain(image_name=image_name)
        qu = '''
            INSERT INTO template_vm (id) VALUES ($1)
            ''', domain['id']
        await conn.fetch(*qu)
        return CreateTemplate(id=domain['id'])


class AddTemplate(graphene.Mutation):
    class Arguments:
        id = graphene.String()

    ok = graphene.Boolean()

    @db.connect()
    async def mutate(self, info, id, conn: Connection):
        qu = '''
            INSERT INTO vm (id, is_template) VALUES ($1, $2)
            ''', id, True
        await conn.fetch(*qu)
        return AddTemplate(ok=True)



class PoolMutations(graphene.ObjectType):
    addPool = AddPool.Field()
    launchPool = LaunchPool.Field()
    createTemplate = CreateTemplate.Field()
    addTemplate = AddTemplate.Field()

from graphql.execution.executors.asyncio import AsyncioExecutor

schema = graphene.Schema(query=PoolQuery, mutation=PoolMutations, auto_camelcase=False)

app.add_route('/admin', GraphQLApp(schema, executor_class=AsyncioExecutor))




