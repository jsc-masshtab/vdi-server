import asyncio
import json
from typing import List

import graphene
from cached_property import cached_property as cached
from classy_async import wait
from vdi.settings import settings as settings_file
from vdi.tasks import vm
from vdi.tasks.resources import DiscoverController


from .users import UserType
from .util import get_selections
from ..db import db
from ..pool import Pool

from vdi.errors import SimpleError, FieldError


class TemplateType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    info = graphene.String(get=graphene.String())

    @graphene.Field
    def node():
        from vdi.graphql.resources import NodeType
        return NodeType

    def resolve_info(self, info, get=None):
        info = self.info
        if get:
            for part in get.split('.'):
                try:
                    part = int(part)
                except ValueError:
                    info = info.get(part)
                    if info is None:
                        return None
                else:
                    try:
                        info = info[part]
                    except:
                        return None
        if get and isinstance(info, str):
            pass
        else:
            info = json.dumps(info)
        return info


class RunningState(graphene.Enum):
    RUNNING = 1
    STOPPED = 0

class PoolType(graphene.ObjectType):
    #TODO rm settings, add controller, cluster, datapool, etc.

    id = graphene.Int()
    template_id = graphene.String(required=True)
    name = graphene.String()
    settings = graphene.Field(lambda: PoolSettings)
    state = graphene.Field(lambda: PoolState)
    users = graphene.List(UserType)
    vms = graphene.List(lambda: VmType)

    @graphene.Field
    def controller():
        from vdi.graphql.resources import ControllerType
        return ControllerType

    sql_fields = ['id', 'template_id', 'initial_size', 'reserve_size', 'name', 'controller_ip']

    def resolve_state(self, info):
        if self.id not in Pool.instances:
            state = PoolState(running=RunningState.STOPPED, pool=self)
            return state
        pool = Pool.instances[self.id]
        state = PoolState(running=RunningState.RUNNING, pool=self)
        return state

    async def resolve_vms(self, info):
        state = self.resolve_state(None)
        vms = await state.resolve_available(info)
        return vms

class VmState(graphene.Enum):
    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class VmType(graphene.ObjectType):
    name = graphene.String()
    id = graphene.String()
    info = graphene.String(deprecation_reason="Use `template {info}`")
    template = graphene.Field(TemplateType)
    user = graphene.Field(UserType)
    state = graphene.Field(VmState)
    pool = graphene.Field(PoolType)

    #TODO cached info?

    selections: List[str]
    sql_data: dict = None


    @cached
    def controller_ip(self):
        return self.pool.controller.ip

    async def get_sql_data(self):
        sql_fields = {'template', 'user'}
        sql_fields = set(self.selections) & sql_fields
        sql_selections = [
            {'template': 'template_id', 'user': 'username'}.get(f, f)
            for f in sql_fields
        ]
        async with db.connect() as conn:
            data = await conn.fetch(f"select {', '.join(sql_selections)} from vm where id = $1", self.id)
            if not data:
                return None
            [data] = data
            return dict(data.items())

    @graphene.Field
    def node():
        from vdi.graphql.resources import NodeType
        return NodeType

    async def resolve_user(self, info):
        if self.sql_data is None:
            self.sql_data = await self.get_sql_data()
        username = self.sql_data['username']
        return UserType(username=username)

    async def resolve_node(self, info):
        selected = get_selections(info)
        for key in selected:
            if not hasattr(self.node, key):
                break
        else:
            return self.node
        from vdi.tasks.resources import FetchNode
        from vdi.graphql.resources import NodeType
        node = await FetchNode(controller_ip=self.controller_ip, node_id=self.node.id)
        from vdi.graphql.resources import ControllerType
        controller = ControllerType(ip=self.controller_ip)
        obj = controller._make_type(NodeType, node)
        obj.controller = controller
        return obj

    async def resolve_template(self, info):
        if self.template:
            # TODO make sure all fields are available
            return self.template
        if self.sql_data is None:
            self.sql_data = await self.get_sql_data()
        template_id = self.sql_data['template_id']
        if get_selections(info) == ['id']:
            return TemplateType(id=template_id)
        from vdi.tasks.vm import GetDomainInfo
        template = await GetDomainInfo(controller_ip=self.controller_ip, domain_id=template_id)
        return TemplateType(id=template_id, info=template, name=template['verbose_name'])

    async def resolve_state(self, info):
        if self.info is None:
            from vdi.tasks.vm import GetDomainInfo
            self.info = await GetDomainInfo(controller_ip=self.controller_ip, domain_id=self.id)
        val = self.info['user_power_state']
        return VmState.get(val)

    info: dict = None


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
    pool = graphene.Field(PoolType)

    @cached
    def controller_ip(self):
        return self.pool.controller.ip

    async def resolve_available(self, info):
        async with db.connect() as conn:
            qu = 'select node_id from pool where id = $1', self.pool.id
            data = await conn.fetch(*qu)
            if not data:
                return []
            [(node_id,)] = await conn.fetch(*qu)
            qu = 'select id, template_id from vm where pool_id = $1', self.pool.id
            data = await conn.fetch(*qu)
        if not data:
            return []
        vm_ids, template_ids = zip(*data)
        [template_id] = set(template_ids)
        vms = await vm.ListVms(controller_ip=self.controller_ip)
        vms = [
            vm for vm in vms if vm['id'] in set(vm_ids)
        ]
        from vdi.graphql.vm import TemplateType
        from vdi.graphql.resources import NodeType

        template_selections = get_selections(info, 'template') or ()
        if {'id', *template_selections} > {'id'}:
            from vdi.tasks.vm import GetDomainInfo
            template = await GetDomainInfo(controller_ip=self.controller_ip, domain_id=template_id)
            template = TemplateType(id=template_id, info=template, name=template['verbose_name'])
        else:
            template = TemplateType(id=template_id)
        li = []
        for domain in vms:
            node = NodeType(id=node_id)
            obj = VmType(id=domain['id'], template=template, name=domain['verbose_name'], node=node, pool=self.pool)
            obj.selections = get_selections(info)
            li.append(obj)
        return li

# TODO dict of pending tasks


class AddPool(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

        template_id = graphene.String()
        cluster_id = graphene.String()
        datapool_id = graphene.String()
        node_id = graphene.String()
        settings = PoolSettingsInput()
        initial_size = graphene.Int()
        reserve_size = graphene.Int()

        block = graphene.Boolean()

    Output = PoolType




    async def mutate(self, info, name,
                     template_id=None, cluster_id=None, datapool_id=None, node_id=None,
                     settings=(), initial_size=None, reserve_size=None):
        def get_setting(name):
            if name in settings:
                return settings[name]
            return settings_file['pool'][name]

        pool = {
            'initial_size': initial_size or get_setting('initial_size'),
            'reserve_size': reserve_size or get_setting('reserve_size'),
            'cluster_id': cluster_id or settings['cluster_id'],
            'node_id': node_id or settings['node_id'],
            'datapool_id': datapool_id or settings['datapool_id'],
            'template_id': template_id or settings['template_id'],
            'name': name,
        }

        controller_ip = await DiscoverController(cluster_id=pool['cluster_id'], node_id=pool['node_id'])
        if not controller_ip:
            raise FieldError(cluster_id=['Неверное значение или не соответствует node_id'],
                             node_id=['Неверное значение или не соответствует cluster_id'])
        pool['controller_ip'] = controller_ip
        fields = ', '.join(pool.keys())
        values = ', '.join(f'${i+1}' for i in range(len(pool)))
        pool_query = f"INSERT INTO pool ({fields}) VALUES ({values}) RETURNING id", *pool.values()
        async with db.connect() as conn:
            [res] = await conn.fetch(*pool_query)
        pool['id'] = res['id']
        ins = Pool(params=pool)
        Pool.instances[pool['id']] = ins

        settings = PoolSettings(**{
            'initial_size': pool['initial_size'],
            'reserve_size': pool['reserve_size'],
        })
        add_domains = ins.add_domains()
        selections = get_selections(info)
        if 'vms' in selections:
            breakpoint()
            domains = await add_domains
            from vdi.graphql.vm import TemplateType
            from vdi.graphql.resources import NodeType
            available = []
            for domain in domains:
                template = domain['template']
                node = NodeType(id=template['node']['id'], verbose_name=template['node']['verbose_name'])
                template = TemplateType(id=template['id'], info=template, name=template['verbose_name'])
                item = VmType(id=domain['id'], template=template, name=domain['verbose_name'], node=node)
                item.info = domain
                item.selections = get_selections(info)
                available.append(item)
        else:
            asyncio.create_task(add_domains)
            available = []
        state = PoolState(available=available, running=True)
        from vdi.graphql.resources import ControllerType
        ret = PoolType(id=pool['id'], state=state, settings=settings, name=name, template_id=pool['template_id'],
                       controller=ControllerType(ip=controller_ip))
        state.pool = ret
        for item in available:
            item.pool = ret

        return ret


class WakePool(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()

    async def mutate(self, info, id):
        from vdi.pool import Pool
        await Pool.wake_pool(id)
        return WakePool(ok=True)


# TODO list of vms
# TODO delete, drop, remove: use a single word

class RemovePool(graphene.Mutation):
    class Arguments:
        id = graphene.Int()
        controller_ip = graphene.String()
        block = graphene.Boolean()

    ok = graphene.Boolean()
    ids = graphene.List(graphene.String)
    #TODO VmType

    @classmethod
    async def do_remove(cls, pool_id, *, controller_ip):
        pool = await Pool.get_pool(pool_id)
        vms = await pool.load_vms()
        vm_ids = [v['id'] for v in vms]

        tasks = [
            vm.DropDomain(id=vm_id, controller_ip=controller_ip)
            for vm_id in vm_ids
        ]

        async with db.connect() as conn:
            qu = "update pool set deleted=TRUE where id = $1", pool_id
            await conn.fetch(*qu)

        async for _ in wait(*tasks):
            pass

        # remove from db
        async with db.connect() as conn:
            # TODO what if there are extra vms in db?
            await conn.fetch("DELETE FROM vm WHERE pool_id = $1", pool_id)
            await conn.fetch("DELETE FROM pool WHERE id = $1", pool_id)
        Pool.instances.pop(pool_id, None)

        return vm_ids

    async def mutate(self, info, id, block=False):
        async with db.connect() as conn:
            qu = 'select controller_ip from pool where id = $1', id
            (controller_ip,) = await conn.fetch(*qu)
        task = RemovePool.do_remove(id, controller_ip=controller_ip)
        task = asyncio.create_task(task)
        selections = get_selections(info)
        if block or 'ids' in selections:
            vm_ids = await task
            return RemovePool(ok=True, ids=vm_ids)
        return RemovePool(ok=True)



class PoolMixin:
    pools = graphene.List(PoolType, controller_ip=graphene.String())
    pool = graphene.Field(PoolType, id=graphene.Int(), name=graphene.String(),
                          controller_ip=graphene.String())


    #TODO wake pools

    async def _select_pool(self, info, id, name):
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
        async with db.connect() as conn:
            [pool] = await conn.fetch(*qu)
        dic = {
            f: pool[f] for f in fields
        }
        settings = {}
        for sel in settings_selections:
            settings[sel] = pool[sel]
        dic['settings'] = PoolSettings(**settings)
        return dic

    async def resolve_pool(self, info, id=None, name=None):
        #TODO will be refactored

        dic = await PoolMixin._select_pool(self, info, id, name)
        if not id:
            id = dic['id']
        async with db.connect() as conn:
            [(controller_ip,)] = await conn.fetch('select controller_ip from pool where id = $1', id)
        u_fields = get_selections(info, 'users') or ()
        u_fields_joined = ', '.join(f'u.{f}' for f in u_fields)
        if u_fields:
            async with db.connect() as conn:
                qu = f"""
                SELECT {u_fields_joined}
                FROM pools_users JOIN public.user as u ON  pools_users.username = u.username
                WHERE pool_id = $1
                """, id
                data = await conn.fetch(*qu)
            users = []
            for u in data:
                u = dict(zip(u_fields, u))
                users.append(UserType(**u))
            dic['users'] = users
        from vdi.graphql.resources import ControllerType
        return PoolType(id=id, **dic, controller=ControllerType(ip=controller_ip))

    #TODO fix users
    #TODO remove this
    async def get_pools_users_map(self, u_fields):
        u_fields_prefixed = [f'u.{f}' for f in u_fields]
        fields = ['pool_id'] + u_fields_prefixed
        qu = f"""
            SELECT {', '.join(fields)}
            FROM pools_users LEFT JOIN public.user as u ON pools_users.username =  u.username
            """
        map = {}
        async with db.connect() as conn:
            records = await conn.fetch(qu)
        for pool_id, *values in records:
            u = dict(zip(u_fields, values))
            map.setdefault(pool_id, []).append(UserType(**u))
        return map


    #FIXME use resolve
    async def resolve_pools(self, info):
        selections = get_selections(info)
        settings_selections = get_selections(info, 'settings') or []
        fields = [
            f for f in selections
            if f in PoolType.sql_fields and f != 'id'
        ]
        fields = ['id', 'controller_ip'] + fields
        qu = f"SELECT {', '.join(fields + settings_selections)} FROM pool WHERE deleted IS NOT TRUE"
        async with db.connect() as conn:
            pools = await conn.fetch(qu)

        u_fields = get_selections(info, 'users')
        if u_fields:
            pools_users = await PoolMixin.get_pools_users_map(self, u_fields)
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
            controller_ip = p.pop('controller_ip')
            from vdi.graphql.resources import ControllerType
            pt = PoolType(**p, controller=ControllerType(ip=controller_ip))
            items.append(pt)
        return items