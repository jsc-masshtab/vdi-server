import asyncio

import graphene
import json
from asyncpg.connection import Connection
from cached_property import cached_property as cached

from ..db import db
from ..pool import Pool

from .util import get_selections
from .users import UserType

from vdi.tasks import vm
from vdi.asyncio_utils import wait

from vdi.settings import settings as settings_file

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
    users = graphene.List(UserType)

    sql_fields = ['id', 'template_id', 'initial_size', 'reserve_size', 'name']

    @cached
    def pool_id(self):
        raise NotImplementedError

    def resolve_state(self, info):
        if self.pool_id not in Pool.instances:
            return PoolState(running=RunningState.STOPPED)
        state = PoolState(running=RunningState.RUNNING)
        state.pool = Pool.instances[self.pool_id]
        return state


class VmType(graphene.ObjectType):
    name = graphene.String()
    id = graphene.String()
    info = graphene.String()


class PoolSettingsFields(graphene.AbstractType):
    initial_size = graphene.Int()
    reserve_size = graphene.Int()


class PoolSettings(graphene.ObjectType, PoolSettingsFields):
    pass


class PoolSettingsInput(graphene.InputObjectType, PoolSettingsFields):
    pass


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
        template_id = graphene.String(required=True)
        name = graphene.String(required=True)
        settings = PoolSettingsInput(required=False)
        autostart = graphene.Boolean(default_value=True)

    id = graphene.Int()
    name = graphene.String()
    state = graphene.Field(PoolState)
    settings = graphene.Field(PoolSettings)

    @db.transaction()
    async def mutate(self, conn: Connection, info, template_id, name, autostart, settings=()):
        def get_setting(name):
            if name in settings:
                return settings[name]
            return settings_file['pool'][name]

        pool_query = '''
        INSERT INTO pool (template_id, name, initial_size, reserve_size)
        VALUES ($1, $2, $3, $4) RETURNING id
        ''', template_id, name, get_setting('initial_size'), get_setting('reserve_size')
        [res] = await conn.fetch(*pool_query)

        pool = {
            'id': res['id'],
            'name': name,
            'template_id': template_id,
            'initial_size': get_setting('initial_size'),
            'reserve_size': get_setting('reserve_size'),
        }
        running = False
        if autostart:
            ins = Pool(params=pool)
            Pool.instances[pool['id']] = ins
            add_domains = ins.add_domains()
            asyncio.create_task(add_domains)
            running = True
        settings = PoolSettings(**{
            'initial_size': get_setting('initial_size'),
            'reserve_size': get_setting('reserve_size'),
        })
        state = PoolState(pending=0, available=[], running=running)
        return AddPool(id=pool['id'], state=state, settings=settings, name=name)


# TODO list of vms
# TODO delete, drop, remove: use a single word

class RemovePool(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()
    ids = graphene.List(graphene.String)

    @db.connect()
    async def mutate(self, info, id, conn: Connection):
        qu = f'''
        SELECT vm.id FROM vm JOIN pool ON vm.pool_id = pool.id WHERE pool.id = $1
        ''', id
        ids = await conn.fetch(*qu)
        ids = [
            id for (id,) in ids
        ]

        async def drop_vm(id):
            await vm.DropDomain(id=id)
            await conn.fetch("DELETE FROM vm WHERE id = $1)", id)

        tasks = [
            drop_vm(id) for id in ids
        ]
        async for _ in wait(*tasks):
            pass

        await conn.fetch("DELETE FROM pool WHERE id = $1", id)
        return RemovePool(ok=True, ids=ids)



# class LaunchPool(graphene.Mutation):
#     #
#     # development only ?
#     #
#     class Arguments:
#         id = graphene.Int()
#
#     state = graphene.Field(PoolState)
#
#     @db.connect()
#     async def mutate(self, info, id, conn: Connection):
#         if id in Pool.instances:
#             from graphql import GraphQLError
#             raise GraphQLError('pool is launched')
#
#         qu = f'''
#         SELECT pool.id, template_id, name, initial_size, reserve_size, vm.id as "vm.id"
#         FROM pool LEFT JOIN vm
#         ON vm.pool_id = pool.id WHERE pool.id = $1 AND vm.state = 'queued'
#         ''', id
#         records = await conn.fetch(*qu)
#         rec = records[0]
#         dic = {
#             'id': rec['id'],
#             'template_id': rec['template_id'],
#             'name': rec['name'],
#             'initial_size': rec['initial_size'],
#             'reserve_size': rec['reserve_size'],
#         }
#         pool = Pool(params=dic)
#         Pool.instances[id] = pool
#         vms = [
#             {
#                 'id': rec['vm.id'] # TODO: what about vm info?
#             }
#             for rec in records
#         ]
#         for vm in vms:
#             await pool.queue.put(vm)
#             pool.queue.task_done()
#         add_domains = pool.add_domains()
#         asyncio.create_task(add_domains)
#         state = PoolState(running=True)
#         state.pool = pool
#         return LaunchPool(state=state)


class AlterPool(graphene.Mutation):

    def mutate(self, *args):
        # TODO
        pass

    class Arguments:
        id = graphene.Int()


class PoolMixin:
    pools = graphene.List(PoolType)
    pool = graphene.Field(PoolType, id=graphene.Int(required=False), name=graphene.String(required=False))

    async def _select_pool(self, selections, id, name, conn: Connection):
        if id:
            where, param = "WHERE id = $1", id
        else:
            assert name
            where, param = "WHERE name = $1", name
        fields = [
            f for f in selections
            if f in PoolType.sql_fields
        ]
        if not id and 'id' not in fields:
            fields.append('id')

        if not fields:
            return {}

        qu = f"SELECT {', '.join(fields)} FROM pool {where}", param
        [pool] = await conn.fetch(*qu)
        dic = {
            f: pool[f] for f in fields
        }
        return dic

    async def _select_pool_users(self, selections, id, conn: Connection):
        selections = ', '.join(f'u.{s}' for s in selections)
        qu = f"""
        SELECT {selections}
        FROM pools_users JOIN public.user as u ON pools_users.username = u.username
        WHERE pool_id = $1
        """, id

    @db.connect()
    async def resolve_pool(self, info, conn: Connection, id=None, name=None):
        selections = get_selections(info)
        dic = await PoolMixin._select_pool(self, selections, id, name, conn=conn)
        if not id:
            id = dic['id']
        u_fields = get_selections(info, 'users') or ()
        u_fields_joined = ', '.join(f'u.{f}' for f in u_fields)
        if u_fields:
            qu = f"""
            SELECT {u_fields_joined}
            FROM pools_users JOIN public.user as u ON  pools_users.username = u.username
            WHERE pool_id = $1
            """, id
            users = []
            for u in await conn.fetch(*qu):
                u = dict(zip(u_fields, u))
                users.append(UserType(**u))
            dic['users'] = users
        ret = PoolType(**dic)
        ret.pool_id = id

        return ret


    async def get_pools_users_map(self, u_fields, conn: Connection):
        u_fields_prefixed = [f'u.{f}' for f in u_fields]
        fields = ['pool_id'] + u_fields_prefixed
        qu = f"""
            SELECT {', '.join(fields)}
            FROM pools_users LEFT JOIN public.user as u ON pools_users.username =  u.username
            """
        map = {}
        records = await conn.fetch(qu)
        for pool_id, *values in records:
            u = dict(zip(u_fields, values))
            map.setdefault(pool_id, []).append(UserType(**u))
        return map

    @db.connect()
    async def resolve_pools(self, info, conn: Connection):
        selections = get_selections(info)
        fields = [
            f for f in selections
            if f in PoolType.sql_fields and f != 'id'
        ]
        fields.insert(0, 'id')
        qu = f"SELECT {', '.join(fields)} FROM pool"
        pools = await conn.fetch(qu)

        u_fields = get_selections(info, 'users')
        if u_fields:
            pools_users = await PoolMixin.get_pools_users_map(self, u_fields, conn=conn)
        items = []
        for id, *values in pools:
            p = dict(zip(fields, [id] + values))
            if u_fields:
                p['users'] = pools_users[id]
            pt = PoolType(**p)
            pt.pool_id = id
            items.append(pt)
        return items