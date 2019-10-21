import asyncio
import inspect
import json
#import tornado

import graphene
from cached_property import cached_property as cached
from classy_async.classy_async import wait, wait_all
from vdi.settings import settings as settings_file
from vdi.tasks import vm
from vdi.tasks.resources import DiscoverControllerIp, FetchCluster, FetchNode, FetchDatapool
from vdi.tasks.thin_client import EnableRemoteAccess
from vdi.tasks.vm import GetDomainInfo, ListVms

from .users import UserType
from .util import get_selections, check_and_return_pool_data, check_pool_initial_size, check_reserve_size, \
    check_total_size, make_resource_type, remove_vms_from_pool
from db.db import db, fetch
from ..pool import PoolObject, AutomatedPoolManager

from vdi.errors import SimpleError, FieldError, NotFound, FetchException
from vdi.utils import Unset, insert, bulk_insert, validate_name, get_attributes_str # print,

class TemplateType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    veil_info = graphene.String(get=graphene.String())
    info = graphene.String(get=graphene.String())

    @graphene.Field
    def node():
        from vdi.graphql_api.resources import NodeType
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


class DesktopPoolType(graphene.Enum):
    AUTOMATED = 0
    STATIC = 1


# class PoolOrderingArg(graphene.Enum):
#     POOL_NAME = 0
#     CONTROLLER = 1
#     VMS_AMOUNT = 2
#     USERS_AMOUNT = 3
#     POOL_TYPE = 4


class PoolResourcesNames(graphene.ObjectType):
    cluster_name = graphene.String()
    node_name = graphene.String()
    datapool_name = graphene.String()
    template_name = graphene.String()


class PoolType(graphene.ObjectType):
    #TODO rm settings, add controller, cluster, datapool, etc.

    id = graphene.Int()
    template_id = graphene.String()
    desktop_pool_type = graphene.Field(DesktopPoolType)
    name = graphene.String()
    settings = graphene.Field(lambda: PoolSettings)
    state = graphene.Field(lambda: PoolState)
    users = graphene.List(UserType, entitled=graphene.Boolean())
    vms = graphene.List(lambda: VmType)
    pool_resources_names = graphene.Field(PoolResourcesNames)
    status = graphene.String()

    @graphene.Field
    def controller():
        from vdi.graphql_api.resources import ControllerType
        return ControllerType

    sql_fields = ['id', 'template_id', 'name', 'controller_ip', 'desktop_pool_type']

    async def resolve_name(self, info):
        if self.name:
            return self.name
        # get from db if the name is unknown
        async with db.connect() as conn:
            qu = 'SELECT name FROM pool WHERE id = $1', self.id
            pool_name_data = await conn.fetch(*qu)
        if not pool_name_data:
            return None
        [(self.name,)] = pool_name_data
        return self.name

    def resolve_state(self, info):
        if self.id not in AutomatedPoolManager.pool_instances:
            state = PoolState(running=RunningState.STOPPED, pool=self)
            return state
        pool = AutomatedPoolManager.pool_instances[self.id]
        state = PoolState(running=RunningState.RUNNING, pool=self)
        return state

    async def resolve_users(self, _info, entitled=True):

        u_fields = ('username', 'email', 'date_joined')
        # users who are entitled to pool
        if entitled:
            u_fields_joined = ', '.join('u.{}'.format(f) for f in u_fields)
            async with db.connect() as conn:
                qu = """
                SELECT {} 
                FROM pools_users JOIN public.user as u ON pools_users.username = u.username
                WHERE pool_id = {}
                """.format(u_fields_joined, self.id)
                data = await conn.fetch(qu)
        # users who are NOT entitled to pool
        else:
            u_fields_joined = ', '.join('{}'.format(f) for f in u_fields)
            async with db.connect() as conn:
                qu = """
                SELECT {} 
                FROM public.user
                WHERE public.user.username NOT IN
                    (SELECT pools_users.username
                     FROM pools_users
                     WHERE pools_users.pool_id = {}
                    )
                """.format(u_fields_joined, self.id)
                data = await conn.fetch(qu)

        # form list and return
        users = []
        for u in data:
            u = dict(zip(u_fields, u))
            users.append(UserType(**u))
        return users

    async def resolve_vms(self, info):
        vm_selections = get_selections(info)
        try:
            return await self._form_vm_type_list(vm_selections)
        except SimpleError:
            return []

    def resolve_desktop_pool_type(self, _info):
        if isinstance(self.desktop_pool_type, str):
            return getattr(DesktopPoolType, self.desktop_pool_type)
        return self.desktop_pool_type

    async def resolve_settings(self, _info):
        if self.settings:
            return self.settings
        # get settings from db
        async with db.connect() as conn:
            fields = get_attributes_str(PoolSettingsFields)
            qu = "select {} from pool where id = {}".format(fields, self.id)
            [data] = await conn.fetch(qu)
        # create and return object PoolSettings
        pool_type = getattr(DesktopPoolType, data['desktop_pool_type'])
        data = dict(data, desktop_pool_type=pool_type)
        self.settings = PoolSettings(**data)
        return self.settings

    async def resolve_pool_resources_names(self, _info):

        list_of_requested_fields = get_selections(_info)
        # get resources ids from db
        data = await check_and_return_pool_data(self.id)

        # determine names  (looks like code repeat. maybe refactor)
        cluster_name = ''
        if 'cluster_name' in list_of_requested_fields:
            try:
                resp = await FetchCluster(controller_ip=data['controller_ip'], cluster_id=data['cluster_id'])
                cluster_name = resp['verbose_name']
            except NotFound:
                pass

        node_name = ''
        if 'node_name' in list_of_requested_fields:
            try:
                resp = await FetchNode(controller_ip=data['controller_ip'], node_id=data['node_id'])
                node_name = resp['verbose_name']
            except NotFound:
                pass

        datapool_name = ''
        if 'datapool_name' in list_of_requested_fields:
            try:
                resp = await FetchDatapool(controller_ip=data['controller_ip'], datapool_id=data['datapool_id'])
                datapool_name = resp['verbose_name']
            except NotFound:
                pass

        template_name = ''
        if 'template_name' in list_of_requested_fields:
            try:
                resp = await GetDomainInfo(controller_ip=data['controller_ip'], domain_id=data['template_id'])
                template_name = resp['verbose_name']
            except NotFound:
                pass

        return PoolResourcesNames(cluster_name=cluster_name, node_name=node_name,
                                  datapool_name=datapool_name, template_name=template_name)

    async def resolve_status(self, _info):
        # determine pool status. If we cant get veil info about at least one vm
        # we consider the pool as broken
        vms = await self._form_vm_type_list(['state'])

        vms_info_list = [single_vm.veil_info for single_vm in vms]
        if Unset in vms_info_list:
            return 'FAILED'
        else:
            return 'ACTIVE'

    async def _form_vm_type_list(self, vm_selections):
        pool_data = await check_and_return_pool_data(self.id)
        all_vms = await ListVms(controller_ip=pool_data['controller_ip'], node_id=pool_data['node_id'])

        async with db.connect() as conn:
            qu = "select id from vm where pool_id = $1", self.id
            data = await conn.fetch(*qu)
        vms = []
        for [vm_id] in data:
            # find veil vm info by id
            try:
                veil_info = next(veil_info for veil_info in all_vms if veil_info['id'] == vm_id)
            except StopIteration:
                veil_info = Unset

            vm_type = VmType(id=vm_id)
            vm_type.veil_info = veil_info
            vm_type.controller_ip = self.controller.ip
            vm_type.selections = vm_selections
            vms.append(vm_type)
        return vms


class VmState(graphene.Enum):
    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3

# WHY IS IT IN THIS FILE
class VmType(graphene.ObjectType):
    name = graphene.String()
    id = graphene.String()
    veil_info = graphene.String()
    template = graphene.Field(TemplateType)
    user = graphene.Field(UserType)
    state = graphene.Field(VmState)
    pool = graphene.Field(PoolType)
    status = graphene.String()

    selections = None #List[str]
    sql_data = Unset
    veil_info = Unset

    @cached
    def controller_ip(self):
        return self.pool.controller.ip

    async def get_sql_data(self): # seems unused. marked for deletion
        sql_fields = {'template', 'user'}
        sql_fields = set(self.selections) & sql_fields
        sql_selections = [
            {'template': 'template_id', 'user': 'username'}.get(f, f)
            for f in sql_fields
        ]
        async with db.connect() as conn:
            sql_request_fields = ', '.join(sql_selections)
            sql_request = """SELECT $1 FROM vm WHERE id = $2""", sql_request_fields, self.id
            print('sql_request', sql_request)
            data = await conn.fetch(*sql_request)
            if not data:
                return None
            [data] = data
            return dict(data.items())

    async def get_veil_info(self):
        from vdi.tasks.vm import GetDomainInfo
        try:
            domain_info = await GetDomainInfo(controller_ip=self.controller_ip, domain_id=self.id)
        except NotFound:
            return None
        else:
            return domain_info

    @graphene.Field
    def node():
        from vdi.graphql_api.resources import NodeType
        return NodeType

    async def resolve_name(self, info):
        if self.name:
            return self.name
        if self.veil_info is Unset:
            self.veil_info = await self.get_veil_info()
        print('self.veil_info', self.veil_info)
        if self.veil_info:
            return self.veil_info['verbose_name']
        else:
            return 'Unknown'

    async def resolve_user(self, info):
        async with db.connect() as conn:
            sql_request = """SELECT username FROM vm WHERE id = $1""", self.id
            [(username,)] = await conn.fetch(*sql_request)
        return UserType(username=username)

    async def resolve_node(self, info):
        selected = get_selections(info)
        for key in selected:
            if not hasattr(self.node, key):
                break
        else:
            return self.node
        from vdi.tasks.resources import FetchNode
        from vdi.graphql_api.resources import NodeType
        node = await FetchNode(controller_ip=self.controller_ip, node_id=self.node.id)
        from vdi.graphql_api.resources import ControllerType
        controller = ControllerType(ip=self.controller_ip)
        obj = make_resource_type(NodeType, node)
        obj.controller = controller
        return obj

    async def resolve_template(self, info):
        if self.template:
            return self.template

        # det data from db
        async with db.connect() as conn:
            sql_request = """SELECT * FROM vm WHERE id = $1""", self.id
            vm_data = await conn.fetch(*sql_request)
        if not vm_data:
            return None

        [vm_data] = vm_data
        template_id = vm_data['template_id']

        # get data from veil
        from vdi.tasks.vm import GetDomainInfo
        try:
            template_data = await GetDomainInfo(controller_ip=self.controller_ip, domain_id=template_id)
            template_name = template_data['verbose_name']
        except NotFound:
            template_data = None
            template_name = ''

        return TemplateType(id=template_id, veil_info=template_data, name=template_name)

    async def resolve_state(self, _info):
        if self.veil_info is Unset:
            self.veil_info = await self.get_veil_info()
        if self.veil_info:
            val = self.veil_info['user_power_state']
            return VmState.get(val)
        else:
            return VmState.UNDEFINED

    async def resolve_pool(self, _info):
        # get pool id from db
        async with db.connect() as conn:
            sql_request = """SELECT pool_id FROM vm WHERE id = $1""", self.id
            pool_id_data = await conn.fetch(*sql_request)

        if not pool_id_data:
            return None
        [(pool_id,)] = pool_id_data

        return PoolType(id=pool_id)

    async def resolve_status(self, _info):
        if self.veil_info is Unset:
            self.veil_info = await self.get_veil_info()
        if self.veil_info:
            return self.veil_info['status']
        else:
            return 'Unknown'


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
        from vdi.graphql_api.vm import TemplateType
        from vdi.graphql_api.resources import NodeType, ControllerType

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
            raise SimpleError('Неверное значение или не соответствует node_id'
                              'Неверное значение или не соответствует cluster_id')
        return controller_ip

    async def validate_async(self, name, val):
        try:
            method = getattr(self, name)
            result = await method(name, val)
        except ValidationError as ex:
            raise SimpleError('Ошибка валидации пула')
        if result is not None:
            self._pool[name] = result

    def validate_sync(self, name, val):
        try:
            method = getattr(self, name)
            result = method(name, val)
        except ValidationError as ex:
            raise SimpleError('Ошибка валидации пула')
        if result is not None:
            self._pool[name] = result

    @staticmethod
    def validate_pool_name(pool_name):
        if not pool_name:
            raise SimpleError('Имя пула не должно быть пустым')
        if not validate_name(pool_name):
            raise SimpleError('Имя пула должно содержать только буквы и цифры')


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
        controller_ip = graphene.String(required=True)

    Output = PoolType
    # ok = graphene.Boolean() # todo: how must be

    @staticmethod
    async def magic_checks(pool):
        # magic checks from Vitalya. Nobody can understand this
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

    @staticmethod
    def validate_agruments(pool_args_dict):
        PoolValidator.validate_pool_name(pool_args_dict['name'])
        # Check vm_name_template if its not empty
        vm_name_template = pool_args_dict['vm_name_template']
        if vm_name_template and not validate_name(vm_name_template):
            raise SimpleError('Шаблонное имя вм должно содержать только буквы и цифры')

        # check sizes
        initial_size = pool_args_dict['initial_size']
        reserve_size = pool_args_dict['reserve_size']
        total_size = pool_args_dict['total_size']
        check_pool_initial_size(initial_size)
        check_reserve_size(reserve_size)
        check_total_size(total_size, initial_size)

        if pool_args_dict['controller_ip'] is None:
            raise SimpleError('Не указан ip контроллера')

    @staticmethod
    def get_setting(name, settings, kwargs):
        if name in kwargs:
            return kwargs[name]
        if name in settings:
            return settings[name]
        if name in settings_file['pool']:
            return settings_file['pool'][name]
        return None

    async def mutate(self, _info, settings=(), **kwargs):

        # form pool arguments dictionary
        pool_settings = {
            k: AddPool.get_setting(k, settings, kwargs)
            for k in PoolSettings._meta.fields
        }
        pool_settings['desktop_pool_type'] = DesktopPoolType.AUTOMATED.name
        pool_args_dict = {
            'name': kwargs['name'],
            'controller_ip': kwargs.get('controller_ip'),
            **pool_settings
        }

        # validate arguments
        #AddPool.magic_checks(pool)
        AddPool.validate_agruments(pool_args_dict)

        # add to db
        pool_data = {
            **{k: v for k, v in pool_args_dict.items() if k in AutomatedPoolManager.pool_keys}
        }
        [[pool_id]] = await insert('pool', pool_data, returning='id')

        # add to AutomatedPoolManager.pool_instances
        pool_object = PoolObject(pool_args_dict)
        pool_object.params['id'] = pool_id
        AutomatedPoolManager.pool_instances[pool_id] = pool_object

        # start vm-creating coroutine
        loop = asyncio.get_event_loop()
        loop.create_task(pool_object.add_initial_vms())  # todo: think about cancelation

        # send positive response (pool creating started)
        #return {'ok': True} # todo: how must be
        # left for VDi front old style compatibility
        from vdi.graphql_api.resources import NodeType, ControllerType
        controller = ControllerType(ip=pool_args_dict['controller_ip'])

        state = PoolState(available=[], running=True)
        pool_type = PoolType(id=pool_id, state=state,
                             name=pool_args_dict['name'], template_id=pool_args_dict['template_id'],
                             controller=controller,
                             settings=PoolSettings(**pool_settings),
                             desktop_pool_type=DesktopPoolType.AUTOMATED,
                             vms=[])
        state.pool = pool_type
        return pool_type


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

    @staticmethod
    async def determine_controller_by_vm_id(vm_id):
        async with db.connect() as conn:
            query = "SELECT ip from controller"
            controller_ips = await conn.fetch(query)

        # find controller the vm_id belongs to. If not found then throw exceptetion
        for controller_ip in controller_ips:
            all_vms_on_controller = await vm.ListVms(controller_ip=controller_ip['ip'])
            # create list of vm ids
            all_vm_on_controller_ids = [vmachine['id'] for vmachine in all_vms_on_controller]
            if vm_id in all_vm_on_controller_ids:
                return controller_ip['ip']

        raise SimpleError("Вм не находится ни на одном из известных контроллеров")


    async def mutate(self, _info, vm_ids=None, vm_ids_list=None, **options):
        cls = AddStaticPool
        vm_ids = vm_ids or vm_ids_list
        if not vm_ids:
            raise SimpleError('vm_ids - обязательное поле')

        # validate name
        PoolValidator.validate_pool_name(options['name'])

        # get vm info
        controller_ip = await AddStaticPool.determine_controller_by_vm_id(vm_ids[0])

        #print('controller_ip', controller_ip)
        vm_info = await GetDomainInfo(controller_ip=controller_ip, domain_id=vm_ids[0])
        #print('vm_info', vm_info)
        cluster_id = vm_info['cluster']
        node_id = vm_info['node']['id']

        #  remote access
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
            'cluster_id': cluster_id,
            'node_id': node_id
        }
        [[pool_id]] = await insert('pool', pool, returning='id')
        pool['id'] = pool_id

        # add vms to the database.
        await cls.add_vms_to_pool(vm_ids, pool['id'])
        vms = [
            VmType(id=id) for id in vm_ids
        ]
        from vdi.graphql_api.resources import ControllerType
        settings = PoolSettings(cluster_id=cluster_id, node_id=node_id)
        return PoolType(id=pool['id'], name=pool['name'], vms=vms,
                        controller=ControllerType(ip=pool['controller_ip']),
                        desktop_pool_type=DesktopPoolType.STATIC,
                        settings=settings)


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
            raise SimpleError('vm_ids - обязательное поле')
        # pool checks
        pool_params = await check_and_return_pool_data(pool_id, DesktopPoolType.STATIC.name)
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
                raise SimpleError('ВМ принадлежит другому узлу')
            # check if vm is free (not in any pool)
            if vm_id in used_vm_ids:
                raise SimpleError('ВМ уже находится в одном из пулов')

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

    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise SimpleError('vm_ids - обязательное поле')
        # pool checks
        await check_and_return_pool_data(pool_id, DesktopPoolType.STATIC.name)

        # vms check
        # get list of vms ids which are in pool_id
        async with db.connect() as conn:
            qu = """
              SELECT vm.id from vm JOIN pool ON vm.pool_id = pool.id
              WHERE pool.id = $1
              """, pool_id
            vms_ids_in_pool = await conn.fetch(*qu)
        vms_ids_in_pool = [vm_id['id'] for vm_id in vms_ids_in_pool]
        print('vms_ids_in_pool', vms_ids_in_pool)
        # check if given vm_ids in vms_ids_in_pool
        for vm_id in vm_ids:
            if vm_id not in vms_ids_in_pool:
                raise SimpleError('Одна из ВМ не принадлежит заданному пулу')

        # remove vms
        await remove_vms_from_pool(vm_ids, pool_id)

        return {
            'ok': True
        }


class RemovePool(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()
    ids = graphene.List(graphene.String)

    @classmethod
    async def do_remove(cls, pool_id):
        pool = await AutomatedPoolManager.get_pool(pool_id)
        controller_ip = pool.params['controller_ip']

        try:
            vms = await pool.load_vms()
        except FetchException:
            raise SimpleError('Не удалось получить данные с контроллера')

        # remove from db
        async with db.connect() as conn:
            await conn.fetch("DELETE FROM pools_users WHERE pool_id = $1", pool_id)
            await conn.fetch("DELETE FROM vm WHERE pool_id = $1", pool_id)
            await conn.fetch("DELETE FROM pool WHERE id = $1", pool_id)

        vm_ids = [v['id'] for v in vms]

        if pool.params['desktop_pool_type'] == DesktopPoolType.AUTOMATED.name:
            for vm_id in vm_ids:
                await vm.DropDomain(id=vm_id, controller_ip=controller_ip)

        AutomatedPoolManager.pool_instances.pop(pool_id, None)

        return vm_ids

    async def mutate(self, info, id):
        task = RemovePool.do_remove(id)

        loop = asyncio.get_event_loop()
        task = loop.create_task(task)
        #task = asyncio.create_task(task) # python 3.7

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
            raise SimpleError("Можно указать только пользователей или только роли в одном запросе")
        for vm in freed:
            vm.controller_ip = controller_ip
        return cls(freed=freed)


class PoolMixin:
    pools = graphene.List(PoolType, ordering=graphene.String(), reversed_order=graphene.Boolean())
    pool = graphene.Field(PoolType, id=graphene.Int(),
                          controller_ip=graphene.String())


    async def _select_pool(self, info, id):
        settings_selections = get_selections(info, 'settings') or []

        qu = "select * from pool where id = $1", id
        async with db.connect() as conn:
            [pool] = await conn.fetch(*qu)
        dic = dict(pool.items())
        # settings = {}
        # for sel in settings_selections:
        #     settings[sel] = pool[sel]
        # dic['settings'] = PoolSettings(**settings)
        return dic

    async def resolve_pool(self, info, id):
        #TODO will be refactored

        pool_data = await PoolMixin._select_pool(self, info, id)
        print('pool_data', pool_data)
        controller_ip = pool_data['controller_ip']

        from vdi.graphql_api.resources import ControllerType
        pool_data['id'] = id
        pool_data = {
            k: v for k, v in pool_data.items() if k in PoolType._meta.fields
        }
        return PoolType(**pool_data,
                        controller=ControllerType(ip=controller_ip))

    async def resolve_pools(self, _info, ordering=None, reversed_order=None):

        # sort items if required
        if ordering:
            # is reversed
            if reversed_order is not None:
                sort_order = 'DESC' if reversed_order else 'ASC'
            else:
                sort_order = 'ASC'

            # determine sql query
            if ordering == 'pool_name':
                qu = "SELECT * FROM pool WHERE deleted IS NOT true ORDER BY name {}".format(sort_order)
            elif ordering == 'controller':
                qu = "SELECT * FROM pool WHERE deleted IS NOT true ORDER BY controller_ip {}".format(sort_order)
            elif ordering == 'vms_amount':
                qu = "SELECT pool.* FROM pool LEFT JOIN vm " \
                     "ON pool.id = vm.pool_id GROUP BY pool.id ORDER BY COUNT(vm.id) {}".format(sort_order)
            elif ordering == 'users_amount':
                qu = "SELECT pool.* FROM pool LEFT JOIN pools_users " \
                     "ON pool.id = pools_users.pool_id GROUP BY pool.id ORDER BY COUNT(pools_users.username)" \
                     " {}".format(sort_order)
            elif ordering == 'pool_type':
                qu = "SELECT * FROM pool WHERE deleted IS NOT true ORDER BY desktop_pool_type {}".format(sort_order)
            else:
                raise SimpleError('Неверный параметр сортировки')
        else:
            qu = "SELECT * FROM pool WHERE deleted IS NOT true"

        # get from db
        async with db.connect() as conn:
            pools = await conn.fetch(qu)

        # create list of items
        items = []
        for pool in pools:
            pool = dict(pool.items())
            controller_ip = pool['controller_ip']
            p = {
                f: pool[f] for f in pool
                if f in PoolType._meta.fields
            }
            settings = {
                f: pool[f] for f in pool
                if f in PoolSettings._meta.fields
            }

            from vdi.graphql_api.resources import ControllerType
            pool_type = PoolType(**p,
                          settings=PoolSettings(**settings),
                          controller=ControllerType(ip=controller_ip))
            items.append(pool_type)

        return items


class ChangePoolName(graphene.Mutation):
    class Arguments:
        pool_id = graphene.Int(required=True)
        new_name = graphene.String(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, pool_id, new_name):
        await check_and_return_pool_data(pool_id)
        # check if name is correct
        PoolValidator.validate_pool_name(new_name)
        # set name
        async with db.connect() as conn:
            qu = 'UPDATE pool SET name = $1 WHERE id = $2', new_name, pool_id
            await conn.fetch(*qu)

        return {'ok': True}


class ChangeVmNameTemplate(graphene.Mutation):
    class Arguments:
        pool_id = graphene.Int(required=True)
        new_name_template = graphene.String(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, pool_id, new_name_template):
        await check_and_return_pool_data(pool_id, DesktopPoolType.AUTOMATED.name)
        # check if name is correct
        PoolValidator.validate_pool_name(new_name_template)
        # set name
        async with db.connect() as conn:
            qu = 'UPDATE pool SET vm_name_template = $1 WHERE id = $2', new_name_template, pool_id
            await conn.fetch(*qu)

        # change live data
        if pool_id in AutomatedPoolManager.pool_instances and \
                'vm_name_template' in AutomatedPoolManager.pool_instances[pool_id].params:
            AutomatedPoolManager.pool_instances[pool_id].params['vm_name_template'] = new_name_template

        return {'ok': True}


class ChangeAutomatedPoolTotalSize(graphene.Mutation):
    class Arguments:
        pool_id = graphene.Int(required=True)
        new_total_size = graphene.Int(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, pool_id, new_total_size):
        pool_data_dict = await check_and_return_pool_data(pool_id, DesktopPoolType.AUTOMATED.name)
        check_total_size(new_total_size, pool_data_dict['initial_size'])
        #  do nothing
        if pool_data_dict['total_size'] == new_total_size:
            return {'ok': True}

        # set total size in db
        async with db.connect() as conn:
            qu = 'UPDATE pool SET total_size = $1 WHERE id = $2', new_total_size, pool_id
            await conn.fetch(*qu)

        # live data
        if pool_id in AutomatedPoolManager.pool_instances and \
                'total_size' in AutomatedPoolManager.pool_instances[pool_id].params:
            AutomatedPoolManager.pool_instances[pool_id].params['total_size'] = new_total_size

        # change amount of created vms
        vm_amount_in_pool = await PoolObject.get_vm_amount_in_pool(pool_id)
        #  decreasing (in this case we need to remove machines if there are too many of them)
        if new_total_size < vm_amount_in_pool:
            vm_amount_delta = vm_amount_in_pool - new_total_size

            # delete from db
            async with db.connect() as conn:
                qu = 'SELECT * FROM vm WHERE pool_id = $1 LIMIT $2', pool_id, vm_amount_delta
                vm_data = await conn.fetch(*qu)
                vm_ids = [single_vm['id'] for single_vm in vm_data]
                # delete
                await remove_vms_from_pool(vm_ids, pool_id)
                await conn.fetch(*qu)

            # delete on controller
            controller_ip = pool_data_dict['controller_ip']
            for vm_id in vm_ids:
                await vm.DropDomain(id=vm_id, controller_ip=controller_ip)

        return {'ok': True}


class ChangeAutomatedPoolReserveSize(graphene.Mutation):
    class Arguments:
        pool_id = graphene.Int(required=True)
        new_reserve_size = graphene.Int(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, pool_id, new_reserve_size):
        pool_data_dict = await check_and_return_pool_data(pool_id, DesktopPoolType.AUTOMATED.name)
        check_reserve_size(pool_data_dict['reserve_size'])
        #  do nothing
        if pool_data_dict['reserve_size'] == new_reserve_size:
            return {'ok': True}
        # set reserve size in db
        async with db.connect() as conn:
            qu = 'UPDATE pool SET reserve_size = $1 WHERE id = $2', new_reserve_size, pool_id
            await conn.fetch(*qu)

        return {'ok': True}
