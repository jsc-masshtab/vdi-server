import asyncio

import graphene
import json
from asyncpg.connection import Connection
from cached_property import cached_property as cached

from ..db import db
from ..pool import Pool

from .util import get_selections
from .users import UserType


class TemplateType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    info = graphene.String()


# TODO TemplateType == VmType

from vdi.tasks import vm

from classy_async import wait
from vdi.context_utils import enter_context

from vdi.settings import settings as settings_file

class RunningState(graphene.Enum):
    RUNNING = 1
    STOPPED = 0

class PoolType(graphene.ObjectType):
    id = graphene.Int()
    template_id = graphene.String(required=True)
    name = graphene.String()
    settings = graphene.Field(lambda: PoolSettings)
    state = graphene.Field(lambda: PoolState)
    users = graphene.List(UserType)

    sql_fields = ['id', 'template_id', 'initial_size', 'reserve_size', 'name']

    @cached
    def pool_id(self):
        raise NotImplementedError

    def resolve_state(self, info):
        if self.pool_id not in Pool.instances:
            return PoolState(running=RunningState.STOPPED)
        pool = Pool.instances[self.pool_id]
        available = PoolState.get_available(pool)
        state = PoolState(running=RunningState.RUNNING, available=available)
        return state


class VmType(graphene.ObjectType):
    name = graphene.String()
    id = graphene.String()
    info = graphene.String()
    template = graphene.Field(TemplateType)


class PoolSettingsFields(graphene.AbstractType):
    controller_ip = graphene.String()
    cluster_id = graphene.String()
    datapool_id = graphene.String()
    template_id = graphene.String()
    node_id = graphene.String()
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

    async def resolve_pending(self, info):
        if self.pool is None:
            return None
        return self.pool.pending

    @classmethod
    def get_available(cls, pool):
        from vdi.graphql.vm import TemplateType
        if pool is None:
            return []
        qu = pool.queue._queue
        li = []
        for item in qu:
            template = item['template']
            template = TemplateType(id=template['id'], info=template, name=template['verbose_name'])
            obj = VmType(id=item['id'], template=template)
            li.append(obj)
        return li

# TODO dict of pending tasks

class AddPool(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

        template_id = graphene.String()
        controller_ip = graphene.String()
        cluster_id = graphene.String()
        datapool_id = graphene.String()
        node_id = graphene.String()
        settings = PoolSettingsInput()
        initial_size = graphene.Int()
        reserve_size = graphene.Int()

        block = graphene.Boolean()



    id = graphene.Int()
    name = graphene.String()
    state = graphene.Field(PoolState)
    settings = graphene.Field(PoolSettings)

    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info,
                     name,
                     template_id=None, controller_ip=None, cluster_id=None, datapool_id=None, node_id=None,
                     settings=(), initial_size=None, reserve_size=None, block=False):
        def get_setting(name):
            if name in settings:
                return settings[name]
            return settings_file['pool'][name]

        if controller_ip is None and 'controller_ip' not in settings:
            from vdi.graphql.resources import get_controller_ip
            controller_ip = await get_controller_ip()

        pool = {
            'initial_size': initial_size or get_setting('initial_size'),
            'reserve_size': reserve_size or get_setting('reserve_size'),
            'controller_ip': controller_ip or settings['controller_ip'],
            'cluster_id': cluster_id or settings['cluster_id'],
            'node_id': node_id or settings['node_id'],
            'datapool_id': datapool_id or settings['datapool_id'],
            'template_id': template_id or settings['template_id'],
            'name': name,
        }
        fields = ', '.join(pool.keys())
        values = ', '.join(f'${i+1}' for i in range(len(pool)))
        pool_query = f"INSERT INTO pool ({fields}) VALUES ({values}) RETURNING id", *pool.values()

        [res] = await conn.fetch(*pool_query)
        pool['id'] = res['id']
        ins = Pool(params=pool)
        Pool.instances[pool['id']] = ins

        add_domains = ins.add_domains()
        if block:
            domains = await add_domains
            from vdi.graphql.vm import TemplateType
            available = []
            for domain in domains:
                template = domain['template']
                template = TemplateType(id=template['id'], info=template, name=template['verbose_name'])
                item = VmType(id=domain['id'], template=template)
                available.append(item)
        else:
            asyncio.create_task(add_domains)
            available = []
        settings = PoolSettings(**{
            'initial_size': pool['initial_size'],
            'reserve_size': pool['reserve_size'],
        })
        state = PoolState(pending=0, available=available, running=True)
        return AddPool(id=pool['id'], state=state, settings=settings, name=name)


# TODO list of vms
# TODO delete, drop, remove: use a single word

class RemovePool(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()
    ids = graphene.List(graphene.String)

    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info, id):
        pool = await Pool.get_pool(id)
        vms = await pool.load_vms(conn)
        vm_ids = [v['id'] for v in vms]

        #FIXME rename: vm -> domain

        async def drop_vm(vm_id):
            await vm.DropDomain(id=vm_id)
            await conn.fetch("DELETE FROM vm WHERE id = $1", vm_id)

        tasks = [drop_vm(vm_id) for vm_id in vm_ids]
        async for _ in wait(*tasks):
            pass

        await conn.fetch("DELETE FROM pool WHERE id = $1", id)
        return RemovePool(ok=True, ids=vm_ids)



# class AlterPool(graphene.Mutation):
#
#     def mutate(self, id, name, newName):
#         # TODO
#         pass
#
#     class Arguments:
#         id = graphene.String(required=False)
#         name = graphene.String(required=False)
#         newName = graphene.String(required=False)
#         settings = PoolSettingsInput(required=False)
#         block = graphene.Boolean(required=False)


class PoolMixin:
    pools = graphene.List(PoolType)
    pool = graphene.Field(PoolType, id=graphene.Int(required=False), name=graphene.String(required=False))


    #TODO wake pools

    async def _select_pool(self, info, id, name, conn: Connection):
        selections = get_selections(info)
        settings_selections = get_selections(info, 'settings') or []
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

        if not fields and not settings_selections:
            return {}

        qu = f"SELECT {', '.join(fields + settings_selections)} FROM pool {where}", param
        [pool] = await conn.fetch(*qu)
        dic = {
            f: pool[f] for f in fields
        }
        settings = {}
        for sel in settings_selections:
            settings[sel] = pool[sel]
        dic['settings'] = PoolSettings(**settings)
        return dic

    async def _select_pool_users(self, selections, id, conn: Connection):
        selections = ', '.join(f'u.{s}' for s in selections)
        qu = f"""
        SELECT {selections}
        FROM pools_users JOIN public.user as u ON pools_users.username = u.username
        WHERE pool_id = $1
        """, id

    @enter_context(lambda: db.connect())
    async def resolve_pool(conn: Connection, self, info, id=None, name=None):
        dic = await PoolMixin._select_pool(self, info, id, name, conn=conn)
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

    @enter_context(lambda: db.connect())
    async def resolve_pools(conn: Connection, self, info):
        selections = get_selections(info)
        settings_selections = get_selections(info, 'settings') or []
        fields = [
            f for f in selections
            if f in PoolType.sql_fields and f != 'id'
        ]
        fields.insert(0, 'id')
        qu = f"SELECT {', '.join(fields + settings_selections)} FROM pool"

        pools = await conn.fetch(qu)

        u_fields = get_selections(info, 'users')
        if u_fields:
            pools_users = await PoolMixin.get_pools_users_map(self, u_fields, conn=conn)
        items = []
        for pool in pools:
            p = {
                f: pool[f] for f in fields
            }
            settings = {}
            for sel in settings_selections:
                settings[sel] = pool[sel]
            if settings:
                p['settings'] = PoolSettings(**settings)
            if u_fields:
                p['users'] = pools_users[id]
            pt = PoolType(**p)
            pt.pool_id = id
            items.append(pt)
        return items