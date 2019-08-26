import asyncio
import inspect
import json
from dataclasses import dataclass
from typing import List

import graphene
from cached_property import cached_property as cached
from classy_async import wait, wait_all
from vdi.settings import settings as settings_file
from vdi.tasks import vm
from vdi.tasks.resources import DiscoverControllerIp
from vdi.tasks.thin_client import EnableRemoteAccess
from vdi.tasks.vm import GetDomainInfo, GetVdisks

from .users import UserType
from .util import get_selections
from ..db import db, fetch
from ..pool import Pool

from vdi.errors import SimpleError, FieldError
from vdi.utils import Unset, print, insert, bulk_insert


class TemplateType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    veil_info = graphene.String(get=graphene.String())
    info = graphene.String(get=graphene.String())

    @graphene.Field
    def node():
        from vdi.graphql.resources import NodeType
        return NodeType

    def resolve_info(self, info, get=None):
        return self.resolve_veil_info(info, get)

    def resolve_veil_info(self, info, get=None):
        veil_info = self.veil_info
        if get:
            for part in get.split('.'):
                try:
                    part = int(part)
                except ValueError:
                    veil_info = veil_info.get(part)
                    if veil_info is None:
                        return None
                else:
                    try:
                        veil_info = veil_info[part]
                    except:
                        return None
        if get and isinstance(veil_info, str):
            pass
        else:
            veil_info = json.dumps(veil_info)
        return veil_info


class RunningState(graphene.Enum):
    RUNNING = 1
    STOPPED = 0


class DesktopPoolType(graphene.Enum):
    AUTOMATED = 0
    STATIC = 1


class PoolType(graphene.ObjectType):
    #TODO rm settings, add controller, cluster, datapool, etc.

    id = graphene.Int()
    template_id = graphene.String()
    desktop_pool_type = graphene.Field(DesktopPoolType)
    name = graphene.String()
    settings = graphene.Field(lambda: PoolSettings)
    state = graphene.Field(lambda: PoolState)
    users = graphene.List(UserType)
    vms = graphene.List(lambda: VmType)



    @graphene.Field
    def controller():
        from vdi.graphql.resources import ControllerType
        return ControllerType

    sql_fields = ['id', 'template_id', 'name', 'controller_ip', 'desktop_pool_type']

    def resolve_state(self, info):
        if self.id not in Pool.instances:
            state = PoolState(running=RunningState.STOPPED, pool=self)
            return state
        pool = Pool.instances[self.id]
        state = PoolState(running=RunningState.RUNNING, pool=self)
        return state

    async def resolve_vms(self, info):
        if self.vms:
            # static pool
            return self.vms
        # if not self.settings:
        #     await self.resolve_settings(None)
        if self.desktop_pool_type == DesktopPoolType.STATIC:
            async with db.connect() as conn:
                qu = "select id from vm where pool_id = $1", self.id
                data = await conn.fetch(*qu)
            vms = []
            for [vm_id] in data:
                vm = VmType(id=vm_id)
                vm.controller_ip = self.controller.ip
                vm.selections = get_selections(info)
                vms.append(vm)
            return vms
        state = self.resolve_state(None)
        vms = await state.resolve_available(info)
        return vms

    def resolve_desktop_pool_type(self, info):
        if isinstance(self.desktop_pool_type, str):
            return getattr(DesktopPoolType, self.desktop_pool_type)
        return self.desktop_pool_type

    async def resolve_settings(self, info):
        pool_type = self.resolve_desktop_pool_type(None)
        if pool_type == DesktopPoolType.STATIC:
            return None
        if self.settings:
            return self.settings
        async with db.connect() as conn:
            fields = "datapool_id, cluster_id, node_id, template_id, " \
                 "initial_size, reserve_size, controller_ip, desktop_pool_type, " \
                 "vm_name_template, total_size"
            qu = f"select {fields} from pool where id = $1", self.id
            [data] = await conn.fetch(*qu)
        pool_type = getattr(DesktopPoolType, data['desktop_pool_type'])
        data = dict(data, desktop_pool_type=pool_type)
        self.settings = PoolSettings(**data)
        return self.settings

class VmState(graphene.Enum):
    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class VmType(graphene.ObjectType):
    name = graphene.String()
    id = graphene.String()
    veil_info = graphene.String(deprecation_reason="Use `template {info}`")
    template = graphene.Field(TemplateType)
    user = graphene.Field(UserType)
    state = graphene.Field(VmState)
    pool = graphene.Field(PoolType)

    #TODO cached info?

    selections: List[str]
    sql_data: dict = Unset
    veil_info: dict = Unset


    @cached
    def controller_ip(self):
        return self.pool.controller.ip

    #TODO async_property

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

    async def get_veil_info(self):
        from vdi.tasks.vm import GetDomainInfo
        return await GetDomainInfo(controller_ip=self.controller_ip, domain_id=self.id)

    @graphene.Field
    def node():
        from vdi.graphql.resources import NodeType
        return NodeType

    async def resolve_name(self, info):
        if self.name:
            return self.name
        if self.veil_info is Unset:
            self.veil_info = await self.get_veil_info()
        return self.veil_info['verbose_name']

    async def resolve_user(self, info):
        if self.sql_data is Unset:
            self.sql_data = await self.get_sql_data()
        if not self.sql_data:
            return None
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
        if self.sql_data is Unset:
            self.sql_data = await self.get_sql_data()
        if not self.sql_data:
            return None
        template_id = self.sql_data['template_id']
        if template_id is None:
            return None
            # if self.veil_info is Unset:
            #     self.veil_info = await self.get_veil_info()
            #TODO
        if get_selections(info) == ['id']:
            return TemplateType(id=template_id)
        from vdi.tasks.vm import GetDomainInfo
        template = await GetDomainInfo(controller_ip=self.controller_ip, domain_id=template_id)
        return TemplateType(id=template_id, veil_info=template, name=template['verbose_name'])

    async def resolve_state(self, info):
        if self.veil_info is Unset:
            self.veil_info = await self.get_veil_info()
        val = self.veil_info['user_power_state']
        return VmState.get(val)


class PoolSettingsFields(graphene.AbstractType):
    cluster_id = graphene.String()
    datapool_id = graphene.String()
    template_id = graphene.String()
    node_id = graphene.String()
    initial_size = graphene.Int()
    reserve_size = graphene.Int()
    total_size = graphene.Int()
    vm_name_template = graphene.String()
    desktop_pool_type = graphene.Field(DesktopPoolType)


class PoolSettings(graphene.ObjectType, PoolSettingsFields):

    def resolve_desktop_pool_type(self, info):
        if isinstance(self.desktop_pool_type, str):
            return getattr(DesktopPoolType, self.desktop_pool_type)
        return self.desktop_pool_type


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
            qu = 'select t.node_id ' \
                 'from dynamic_traits as t join pool as p on t.dynamic_traits_id = p.dynamic_traits ' \
                 'where p.id = $1', self.pool.id
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
        from vdi.graphql.resources import NodeType, ControllerType

        template_selections = get_selections(info, 'template') or ()
        if {'id', *template_selections} > {'id'}:
            from vdi.tasks.vm import GetDomainInfo
            template = await GetDomainInfo(controller_ip=self.controller_ip, domain_id=template_id)
            template = TemplateType(id=template_id, veil_info=template, name=template['verbose_name'])
        else:
            template = TemplateType(id=template_id)
        li = []
        for domain in vms:
            node = NodeType(id=node_id, controller=ControllerType(ip=self.controller_ip))
            obj = VmType(id=domain['id'], template=template, name=domain['verbose_name'], node=node, pool=self.pool)
            obj.selections = get_selections(info)
            li.append(obj)
        return li

# TODO dict of pending tasks

class ValidationError(Exception):
    pass


class PoolValidator:
    def __init__(self, pool):
        self._pool = pool

    def initial_size(self, name, val):
        if val is None:
            return settings_file['pool'][name]
        try:
            int(val)
        except ValueError:
            raise ValidationError("Должно быть целочисленным")

    reserve_size = total_size = initial_size

    async def controller_ip(self, name, val):
        if val:
            return val
        controller_ip = await DiscoverControllerIp(cluster_id=self._pool['cluster_id'],
                                                   node_id=self._pool['node_id'])
        if not controller_ip:
            raise FieldError(cluster_id=['Неверное значение или не соответствует node_id'],
                             node_id=['Неверное значение или не соответствует cluster_id'])
        return controller_ip

    async def validate_async(self, name, val):
        try:
            method = getattr(self, name)
            result = await method(name, val)
        except ValidationError as ex:
            raise FieldError(**{name: [str(ex)]})
        if result is not None:
            self._pool[name] = result

    def validate_sync(self, name, val):
        try:
            method = getattr(self, name)
            result = method(name, val)
        except ValidationError as ex:
            raise FieldError(**{name: [str(ex)]})
        if result is not None:
            self._pool[name] = result



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
        total_size = graphene.Int()
        vm_name_template = graphene.String()
        controller_ip = graphene.String()


    Output = PoolType

    async def mutate(self, info, settings=(), **kwargs):

        def get_setting(name):
            if name in kwargs:
                return kwargs[name]
            if name in settings:
                return settings[name]
            if name in settings_file['pool']:
                return settings_file['pool'][name]
            return None

        pool_settings = {
            k: get_setting(k)
            for k in PoolSettings._meta.fields
        }
        pool_settings['desktop_pool_type'] = DesktopPoolType.AUTOMATED.name
        pool = {
            'name': kwargs['name'],
            'controller_ip': kwargs.get('controller_ip'),
            **pool_settings
        }
        checker = PoolValidator(pool)
        data_sync = {}
        data_async = {}
        for k, v in pool.items():
            if hasattr(checker, k):
                if inspect.iscoroutinefunction(getattr(checker, k)):
                    data_async[k] = v
                else:
                    data_sync[k] = v
        for k, v in data_sync.items():
            checker.validate_sync(k, v)
        async_validators = [
            checker.validate_async(k, v) for k, v in data_async.items()
        ]
        await wait_all(*async_validators)

        from vdi.graphql.resources import NodeType, ControllerType
        controller = ControllerType(ip=pool['controller_ip'])

        dyn_traits = {
            k: v for k, v in pool.items() if k in Pool.traits_keys
        }
        [[id]] = await insert('dynamic_traits', dyn_traits, returning='dynamic_traits_id')
        pool_data = {
            'dynamic_traits': id,
            **{k: v for k, v in pool.items() if k in Pool.pool_keys}
        }
        [[pool_id]] = await insert('pool', pool_data, returning='id')
        pool['id'] = pool_id
        ins = Pool(params=pool)
        Pool.instances[pool['id']] = ins

        add_domains = ins.add_domains()
        selections = get_selections(info)
        if 'vms' in selections:
            domains = await add_domains
            from vdi.graphql.vm import TemplateType
            available = []
            for domain in domains:
                template = domain['template']
                node = NodeType(id=template['node']['id'], verbose_name=template['node']['verbose_name'])
                node.controller = controller
                template = TemplateType(id=template['id'], veil_info=template, name=template['verbose_name'])
                item = VmType(id=domain['id'], template=template, name=domain['verbose_name'], node=node)
                item.veil_info = domain
                item.selections = get_selections(info)
                available.append(item)
        else:
            asyncio.create_task(add_domains)
            available = []

        state = PoolState(available=available, running=True)
        ret = PoolType(id=pool['id'], state=state,
                       name=pool['name'], template_id=pool['template_id'],
                       controller=controller,
                       settings=PoolSettings(**pool_settings),
                       desktop_pool_type=DesktopPoolType.AUTOMATED)
        state.pool = ret
        for item in available:
            item.pool = ret

        return ret


async def check_static_pool_and_get_params(cls, pool_id):
    """check if given pool_id corresponds to valid static pool and return its parameters"""
    async with db.connect() as conn:
        qu = f"SELECT * from pool where id = $1", pool_id
        pool_params = await conn.fetch(*qu)
    # check if pool exists
    if not pool_params:
        raise FieldError(pool_id=['Пул с заданным id не существует'])
    # check if pool is static
    [pool_params] = pool_params
    print('pool_params_unpacked', pool_params)
    print('desktop_pool_type', pool_params['desktop_pool_type'])
    if pool_params['desktop_pool_type'] != DesktopPoolType.STATIC.name:
        raise FieldError(pool_id=['Пул с заданным id не является статическим'])

    return pool_params


class AddStaticPool(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        vm_ids_list = graphene.List(graphene.String)
        vm_ids = graphene.List(graphene.ID)

        #deprecated
        datapool_id = graphene.String()
        cluster_id = graphene.String()
        node_id = graphene.String()

    Output = PoolType

    @classmethod
    async def add_vms_to_pool(cls, vm_ids, pool_id):
        rows = [{'id': vm_id, 'pool_id': pool_id}
                for vm_id in vm_ids]
        await bulk_insert('vm', rows)

    @classmethod
    async def get_controller_ip(cls, vm_ids):
        ips = []
        for vm_id in vm_ids[:2]:
            vm_info, controller_ip = await GetDomainInfo(domain_id=vm_id)
            ips.append(controller_ip)
        assert all(ip == ips[0] for ip in ips[1:])
        return ips[0]

    async def mutate(self, _info, vm_ids=None, vm_ids_list=None, **options):
        cls = AddStaticPool
        vm_ids = vm_ids or vm_ids_list
        if not vm_ids:
            raise FieldError(vm_ids=['Обязательное поле'])
        controller_ip = None

        if controller_ip is None:
            controller_ip = await cls.get_controller_ip(vm_ids)

        async with db.connect() as conn:
            qu = (
                "select vm.id from vm join pool on vm.pool_id = pool.id "
                "where pool.desktop_pool_type = 'AUTOMATED' and vm.id = any($1::text[])", list(vm_ids)
            )
            data = await conn.fetch(*qu)
            if data:
                ids = [id for (id,) in data]
                raise SimpleError("Некоторые ВМ принадлежат динамическим пулам")
        tasks = [
            EnableRemoteAccess(controller_ip=controller_ip, domain_id=vm_id)
            for vm_id in vm_ids
        ]
        await wait_all(*tasks)

        # add pool
        pool = {
            'name': options['name'],
            'controller_ip': controller_ip,
            'desktop_pool_type': DesktopPoolType.STATIC.name,
        }
        [[pool_id]] = await insert('pool', pool, returning='id')
        pool['id'] = pool_id

        # add vms to the database.
        await cls.add_vms_to_pool(vm_ids, pool['id'])
        vms = [
            VmType(id=id) for id in vm_ids
        ]
        from vdi.graphql.resources import ControllerType
        return PoolType(id=pool['id'], name=pool['name'], vms=vms,
                        controller=ControllerType(ip=pool['controller_ip']),
                        desktop_pool_type=DesktopPoolType.STATIC)


class AddVmsToStaticPool(graphene.Mutation):
    class Arguments:
        pool_id = graphene.Int(required=True)
        vm_ids = graphene.List(graphene.ID, required=True)

    ok = graphene.Boolean()

    @classmethod
    async def get_list_of_used_vms(cls):
        """get ids list of all vms in pools"""
        async with db.connect() as conn:
            qu = 'SELECT vm.id from vm'
            used_vms = await conn.fetch(qu)
        used_vm_ids = [used_vm['id'] for used_vm in used_vms]
        print('used_vm_ids', used_vm_ids)
        return used_vm_ids

    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise FieldError(vm_ids=['Обязательное поле'])
        # pool checks
        pool_params = await check_static_pool_and_get_params(pool_id)

        # vm checks
        # get list of all vms on the node
        all_vms = await vm.ListVms(controller_ip=pool_params['controller_ip'],
                                   node_id=pool_params['node_id'])
        all_vm_ids = [vmachine['id'] for vmachine in all_vms]
        # get list of vms which are already in pools
        used_vm_ids = await AddVmsToStaticPool.get_list_of_used_vms()

        for vm_id in vm_ids:
            # check if vm exists and it is on the correct node
            if vm_id not in all_vm_ids:
                raise FieldError(vm_ids=['ВМ принадлежит другому узлу'])
            # check if vm is free (not in any pool)
            if vm_id in used_vm_ids:
                raise FieldError(vm_ids=['ВМ уже находится в одном из пулов'])

        # add vms
        await AddStaticPool.add_vms_to_pool(vm_ids, pool_id)
        # remote access
        tasks = [
            EnableRemoteAccess(controller_ip=pool_params['controller_ip'], domain_id=vm_id)
            for vm_id in vm_ids
        ]
        await wait_all(*tasks)

        return {
            'ok': True
        }


class RemoveVmsFromStaticPool(graphene.Mutation):
    class Arguments:
        pool_id = graphene.Int(required=True)
        vm_ids = graphene.List(graphene.ID, required=True)

    ok = graphene.Boolean()

    @classmethod
    async def remove_vms_from_pool(cls, vm_ids, pool_id):
        placeholders = [f'${i + 1}' for i in range(0, len(vm_ids))]
        placeholders = ', '.join(placeholders)
        print('placeholders', placeholders)
        async with db.connect() as conn:
            qu = f'DELETE FROM vm WHERE id IN ({placeholders}) AND pool_id = {pool_id}', *vm_ids
            await conn.fetch(*qu)


    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise FieldError(vm_ids=['Обязательное поле'])
        # pool checks
        await check_static_pool_and_get_params(pool_id)

        # vms check
        # get list of vms ids which are in pool_id
        async with db.connect() as conn:
            qu = f"""
              SELECT vm.id from vm JOIN pool ON vm.pool_id = pool.id
              WHERE pool.id = $1
              """, pool_id
            vms_ids_in_pool = await conn.fetch(*qu)
        vms_ids_in_pool = [vm_id['id'] for vm_id in vms_ids_in_pool]
        print('vms_ids_in_pool', vms_ids_in_pool)
        # check if given vm_ids in vms_ids_in_pool
        for vm_id in vm_ids:
            if vm_id not in vms_ids_in_pool:
                raise FieldError(vm_ids=['Одна из ВМ не принадлежит заданному пулу'])

        # remove vms
        await RemoveVmsFromStaticPool.remove_vms_from_pool(vm_ids, pool_id)

        return {
            'ok': True
        }


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

    ok = graphene.Boolean()
    ids = graphene.List(graphene.String)

    @classmethod
    async def do_remove(cls, pool_id):
        pool = await Pool.get_pool(pool_id)
        controller_ip = pool.params['controller_ip']
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
            await conn.fetch("DELETE FROM pools_users WHERE pool_id = $1", pool_id)
            await conn.fetch("DELETE FROM vm WHERE pool_id = $1", pool_id)
            await conn.fetch("DELETE FROM pool WHERE id = $1", pool_id)
        Pool.instances.pop(pool_id, None)

        return vm_ids

    async def mutate(self, info, id):
        task = RemovePool.do_remove(id)
        task = asyncio.create_task(task)
        selections = get_selections(info)
        if 'ids' in selections:
            vm_ids = await task
            return RemovePool(ok=True, ids=vm_ids)
        return RemovePool(ok=True)


class AddPoolPermissions(graphene.Mutation):

    class Arguments:
        pool_id = graphene.ID()
        users = graphene.List(graphene.ID)
        entitled_users = graphene.List(graphene.ID) # deprecated
        roles = graphene.List(graphene.ID)

    ok = graphene.Boolean()

    @classmethod
    async def handle_users(cls, pool_id, users):
        users = [{'pool_id': pool_id, 'username': user} for user in users]
        await bulk_insert('pools_users', users)

    @classmethod
    async def handle_roles(cls, pool_id, roles):
        roles = [{'pool_id': pool_id, 'role': role} for role in roles]
        await bulk_insert('pool_role_m2m', roles)

    async def mutate(self, _info, pool_id, users=(), entitled_users=(), roles=()):
        cls = AddPoolPermissions
        pool_id = int(pool_id)
        users = users or entitled_users
        if users:
            await cls.handle_users(pool_id, users)
        if roles:
            await cls.handle_roles(pool_id, roles)
        return {'ok': True}



# class AddPoolPermission(graphene.Mutation):
#     class Arguments:
#         pool_id = graphene.ID()
#         users = graphene.List(graphene.ID)
#         groups = graphene.List(graphene.ID)
#
#     async def mutate(self, info, users=(), groups=()):
#         1


class DropPoolPermissions(graphene.Mutation):

    class Arguments:
        pool_id = graphene.ID()
        users = graphene.List(graphene.ID)
        entitled_users = graphene.List(graphene.ID) # deprecated
        roles = graphene.List(graphene.ID)
        free_assigned_vms = graphene.Boolean()

    freed = graphene.List(VmType)

    @classmethod
    async def handle_users(cls, pool_id, users, *, free_assigned_vms):
        async with db.connect() as conn:
            qu = "DELETE FROM pools_users " \
                 "WHERE pool_id = $1 AND username = any($2::text[])", pool_id, users
            await conn.fetch(*qu)
        if not free_assigned_vms:
            return []
        # Find vms no longer permitted to own
        # (owned by users not having the group permission)
        async with db.connect() as conn:
            qu = "select vm.id from vm " \
                 "join user_role_m2m as u_r on vm.username = u_r.username and u_r.username = any($1::text[]) " \
                 "left join pool_role_m2m as p_r on u_r.role = p_r.role and p_r.pool_id = $2 " \
                 "where p_r.role is null", users, pool_id
            data = await conn.fetch(*qu)
            vm_ids = [vm_id for [vm_id] in data]
            qu = "update vm set username = null " \
                 "where id = any($1::text[])", vm_ids
            await conn.fetch(*qu)

        return [VmType(id=vm_id) for vm_id in vm_ids]

    @classmethod
    async def handle_roles(cls, pool_id, roles, *, free_assigned_vms):
        # Remove from permissions
        async with db.connect() as conn:
            qu = "delete from pool_role_m2m " \
                 "where pool_id = $1 and role = any($2::text[])", \
                 pool_id, roles
            await conn.fetch(*qu)
        if not free_assigned_vms:
            return []
        # Find vms no longer permitted to own
        # (owned by users not listed in pools_users)
        async with db.connect() as conn:
            qu = "select vm.id from vm " \
                 "join user_role_m2m as u_r on vm.username = u_r.username and u_r.role = any($1::text[]) " \
                 "left join pools_users as p_u on vm.username = p_u.username and p_u.pool_id = $2 " \
                 "where p_u.username is null", roles, pool_id
            data = await conn.fetch(*qu)
            vm_ids = [vm_id for [vm_id] in data]
            qu = "update vm set username = null " \
                 "where id = any($1::text[])", vm_ids
            await conn.fetch(*qu)
        return [VmType(id=vm_id) for vm_id in vm_ids]

    async def mutate(self, _info, pool_id, entitled_users=(), users=(), roles=(), free_assigned_vms=True):
        cls = DropPoolPermissions
        pool_id = int(pool_id)
        async with db.connect() as conn:
            qu = "select controller_ip from pool where id = $1", pool_id
            [[controller_ip]] = await conn.fetch(*qu)
        users = users or entitled_users
        if users and not roles:
            freed = await cls.handle_users(pool_id, users, free_assigned_vms=free_assigned_vms)
        elif roles and not users:
            freed = await cls.handle_roles(pool_id, roles, free_assigned_vms=free_assigned_vms)
        else:
            raise SimpleError("Можно указать только пользователей или роли")
        for vm in freed:
            vm.controller_ip = controller_ip
        return cls(freed=freed)


class PoolMixin:
    pools = graphene.List(PoolType, controller_ip=graphene.String())
    pool = graphene.Field(PoolType, id=graphene.Int(),
                          controller_ip=graphene.String())


    async def _select_pool(self, info, id):
        selections = get_selections(info)
        settings_selections = get_selections(info, 'settings') or []
        fields = [
            f for f in selections
            if f in PoolType.sql_fields
        ]
        if not id and 'id' not in fields:
            fields.append('id')

        if not fields and not settings_selections:
            return {}

        qu = "select * from pool left join dynamic_traits as t " \
             "on pool.dynamic_traits = t.dynamic_traits_id " \
             "where id = $1", id
        async with db.connect() as conn:
            [pool] = await conn.fetch(*qu)
        dic = dict(pool.items())
        settings = {}
        for sel in settings_selections:
            settings[sel] = pool[sel]
        dic['settings'] = PoolSettings(**settings)
        return dic

    async def resolve_pool(self, info, id):
        #TODO will be refactored

        pool_data = await PoolMixin._select_pool(self, info, id)
        controller_ip = pool_data['controller_ip']
        u_fields = get_selections(info, 'users') or ()
        u_fields_joined = ', '.join(f'u.{f}' for f in u_fields)
        if u_fields:
            async with db.connect() as conn:
                qu = f"""
                SELECT {u_fields_joined}
                FROM pools_users JOIN public.user as u ON pools_users.username = u.username
                WHERE pool_id = $1
                """, id
                data = await conn.fetch(*qu)
            users = []
            for u in data:
                u = dict(zip(u_fields, u))
                users.append(UserType(**u))
            pool_data['users'] = users
        from vdi.graphql.resources import ControllerType
        pool_data['id'] = id
        pool_data = {
            k: v for k, v in pool_data.items() if k in PoolType._meta.fields
        }
        return PoolType(**pool_data,
                        controller=ControllerType(ip=controller_ip))

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


    async def resolve_pools(self, info):
        selections = get_selections(info)
        settings_selections = get_selections(info, 'settings') or []
        fields = [
            f for f in selections
            if f in PoolType.sql_fields and f != 'id'
        ]
        fields = ['id', 'controller_ip'] + fields
        qu = "select * " \
             "from pool left join dynamic_traits as t on pool.dynamic_traits = t.dynamic_traits_id " \
             "where deleted is not true"
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