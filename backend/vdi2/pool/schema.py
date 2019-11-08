# -*- coding: utf-8 -*-
import graphene
import tornado.gen

from tornado.httpclient import HTTPClientError

from common.veil_errors import SimpleError, HttpError
from common.utils import get_selections, validate_name

from settings import MIX_POOL_SIZE, MAX_POOL_SIZE, MAX_VM_AMOUNT_IN_POOL, DEFAULT_NAME

from auth.schema import UserType
from auth.models import User

from vm.schema import VmType, VmQuery
from vm.models import Vm
from vm.veil_client import VmHttpClient

from controller.schema import ControllerType
from controller.models import Controller
from controller_resources.veil_client import ResourcesHttpClient

from pool.models import DesktopPoolType, Pool, PoolUsers


DesktopPoolTypeGraphene = graphene.Enum.from_enum(DesktopPoolType)


# todo: remove raw sql
async def check_and_return_pool_data(pool_id, pool_type=None):
    # check if pool exists
    async with db.connect() as conn:
        qu = 'SELECT * FROM pool WHERE id = $1', pool_id
        pool_data = await conn.fetch(*qu)
        if not pool_data:
            raise SimpleError('Не найден пул с указанным id')
        [pool_data] = pool_data
        pool_data_dict = dict(pool_data.items())

    # if pool_type provided then check if pool has required type
    if pool_type and pool_data_dict['desktop_pool_type'] != pool_type:
        raise SimpleError('Не найден пул с указанным id и типом {}'.format(pool_type))

    return pool_data_dict


def check_pool_initial_size(initial_size):
    if initial_size < MIX_POOL_SIZE or initial_size > MAX_POOL_SIZE:
        raise SimpleError('Начальное количество ВМ должно быть в интервале [{} {}]'.
                          format(MIX_POOL_SIZE, MAX_POOL_SIZE))


def check_reserve_size(reserve_size):
    if reserve_size < MIX_POOL_SIZE or reserve_size > MAX_POOL_SIZE:
        raise SimpleError('Количество создаваемых ВМ должно быть в интервале [{} {}]'.
                          format(MIX_POOL_SIZE, MAX_POOL_SIZE))


def check_total_size(total_size, initial_size):
    if total_size < initial_size:
        raise SimpleError('Максимальное количество создаваемых ВМ не может быть меньше '
                          'начального количества ВМ')
    if total_size < MIX_POOL_SIZE or total_size > MAX_VM_AMOUNT_IN_POOL:
        raise SimpleError('Максимальное количество создаваемых ВМ должно быть в интервале [{} {}]'.
                          format(MIX_POOL_SIZE, MAX_VM_AMOUNT_IN_POOL))


def validate_pool_name(pool_name):
    if not pool_name:
        raise SimpleError('Имя пула не должно быть пустым')
    if not validate_name(pool_name):
        raise SimpleError('Имя пула должно содержать только буквы и цифры')


class PoolResourcesNames(graphene.ObjectType):
    cluster_name = graphene.String()
    node_name = graphene.String()
    datapool_name = graphene.String()
    template_name = graphene.String()


class PoolSettingsFields(graphene.AbstractType):
    cluster_id = graphene.String()
    datapool_id = graphene.String()
    template_id = graphene.String()
    node_id = graphene.String()
    initial_size = graphene.Int()
    reserve_size = graphene.Int()
    total_size = graphene.Int()
    vm_name_template = graphene.String()


class PoolSettings(graphene.ObjectType, PoolSettingsFields):
    pass


class PoolType(graphene.ObjectType):

    id = graphene.String()
    template_id = graphene.String()
    desktop_pool_type = graphene.Field(DesktopPoolTypeGraphene)
    name = graphene.String()
    settings = graphene.Field(PoolSettings)
    users = graphene.List(UserType, entitled=graphene.Boolean())
    vms = graphene.List(VmType)
    pool_resources_names = graphene.Field(PoolResourcesNames)
    status = graphene.String()

    controller = graphene.Field(ControllerType)

    #sql_fields = ['id', 'template_id', 'name', 'controller_ip', 'desktop_pool_type']

    async def resolve_name(self, _info):
        if not self.name:
            self.name = await Pool.get_name(self.id)
        return self.name

    async def resolve_users(self, _info, entitled=True):
        # users who are entitled to pool
        if entitled:
            users_data = await User.join(PoolUsers, User.id == PoolUsers.user_id).select().where(
                 PoolUsers.pool_id == self.id).gino.all()
        # users who are NOT entitled to pool
        else:
            subquery = PoolUsers.query(PoolUsers.user_id).where(PoolUsers.pool_id == self.id)
            users_data = User.filter(User.id.notin_(subquery)).gino.all()
        print('users_data', users_data)
        # todo: it will not work until model and grapnene feilds are syncronized
        uset_type_list = [
            UserType(**user.__values__)
            for user in users_data
        ]
        return uset_type_list

    async def resolve_vms(self, _info):
        await self._build_vms_list()
        return self.vms

    async def resolve_desktop_pool_type(self, _info):
        if not self.desktop_pool_type:
            self.desktop_pool_type = await Pool.get_desktop_type(self.id)
        return self.desktop_pool_type

    async def resolve_settings(self, _info):
        if not self.settings:
            pool_data = await Pool.get_pool_data(self.id)
            # todo: Get data from ORM and just fill PoolSettings
            # ...
            self.settings = PoolSettings()
        return self.settings

    async def resolve_pool_resources_names(self, _info):

        list_of_requested_fields = get_selections(_info)
        # # get resources ids from db
        # data = await check_and_return_pool_data(self.id)
        #
        # todo: determine names
        cluster_name = ''
        node_name = ''
        datapool_name = ''
        template_name = ''

        return PoolResourcesNames(cluster_name=cluster_name, node_name=node_name,
                                  datapool_name=datapool_name, template_name=template_name)

    async def resolve_status(self, _info):

        if not self.status:
            # If we cant receive veil_info about at least one vm then we mark pool as broken
            await self._build_vms_list()
            veil_info_list = [vm.veil_info for vm in self.vms]
            if None in veil_info_list:
                self.status = 'FAILED'
            else:
                self.status = 'ACTIVE'

        return self.status

    async def _build_vms_list(self):
        if not self.vms:
            self.vms = []
            vms_data = await Vm.select("id").where((Vm.pool_id == self.id)).gino.all()
            for (vm_id,) in vms_data:
                vm_http_client = await VmHttpClient.create(self.controller.address, vm_id)
                try:
                    veil_info = await vm_http_client.info()
                    # create graphene type
                    vm_type = VmQuery.veil_vm_data_to_graphene_type(veil_info, self.controller.address)
                except HTTPClientError:
                    vm_type = VmType(id=vm_id, controller=ControllerType(address=self.controller.address))
                    vm_type.veil_info = None
                self.vms.append(vm_type)


class AddStaticPool(graphene.Mutation):
    class Arguments:
        verbose_name = graphene.String(required=True)
        vm_ids = graphene.List(graphene.ID, required=True)

    Output = PoolType

    @staticmethod
    async def fetch_veil_vm_data_list(vm_ids):
        controller_adresses = await Controller.get_controllers_addresses()
        # create list of all vms on controllers
        veil_vm_data_list = []
        for controller_address in controller_adresses:
            vm_http_client = await VmHttpClient.create(controller_address, '')
            try:
                single_vm_veil_data_list = await vm_http_client.fetch_vms_list()
                # add data about controller address
                for vm_veil_data in single_vm_veil_data_list:
                    vm_veil_data['controller_address'] = controller_address
                veil_vm_data_list.extend(single_vm_veil_data_list)
            except (HttpError, OSError):
                pass

        # find vm veil data by id
        vm_veil_data_list = []
        for vm_id in vm_ids:
            try:
                data = next(veil_vm_data for veil_vm_data in veil_vm_data_list if veil_vm_data['id'] == vm_id)
                vm_veil_data_list.append(data)
            except StopIteration:
                raise SimpleError('ВМ с id {} не найдена ни на одном из известных контроллеров'.format(vm_id))

        return vm_veil_data_list

    async def mutate(self, _info, verbose_name, vm_ids):

        # validate name
        validate_pool_name(verbose_name)

        if not vm_ids:
            raise SimpleError("Список ВМ не должен быть пустым")

        # get vm info
        veil_vm_data_list = await AddStaticPool.fetch_veil_vm_data_list(vm_ids)

        # Check that all vms are on the same node (Условие поставленное начальством, насколько я помню)
        first_vm_data = veil_vm_data_list[0]
        if not all(x == first_vm_data for x in veil_vm_data_list):
            raise SimpleError("Все ВМ должны находится на одном сервере")

        # All VMs are on the same node and cluster so we can take this data from the first item
        controller_ip = first_vm_data['controller_address']
        node_id = first_vm_data['node']['id']
        # determine cluster
        resources_http_client = await ResourcesHttpClient.create(controller_ip)
        node_data = await resources_http_client.fetch_node(node_id)
        cluster_id = node_data['cluster']

        # remote access
        async def enable_remote_access(controller_address, vm_id):
            print('enable_remote_access')
            vm_http_client = await VmHttpClient.create(controller_address, vm_id)
            await vm_http_client.enable_remote_access()

        async_tasks = [
            enable_remote_access(controller_address=controller_ip, vm_id=vm_id)
            for vm_id in vm_ids
        ]
        await tornado.gen.multi(async_tasks)  # todo: not tested yet

        # todo: запись в таблицы пулов и вм должна быть одной транзакцией??
        # add pool to db
        controller_uid = await Controller.get_controller_id_by_ip(controller_ip)

        pool = await Pool.create(
            verbose_name=verbose_name,
            status='Ok',
            controller=controller_uid,
            desktop_pool_type=DesktopPoolTypeGraphene.MANUAL.name,
            cluster_id=cluster_id,
            node_id=node_id
        )

        # add vms to the database.
        for vm_id in vm_ids:
            await Vm.create(id=vm_id, pool_id=pool.id)

        # response
        vms = [
            VmType(id=vm_id) for vm_id in vm_ids
        ]
        return PoolType(id=pool.id, name=verbose_name, vms=vms,
                        controller=ControllerType(address=controller_ip),
                        desktop_pool_type=DesktopPoolTypeGraphene.MANUAL)


class PoolQuery(graphene.ObjectType):
    pools = graphene.List(PoolType, ordering=graphene.String(), reversed_order=graphene.Boolean())
    pool = graphene.Field(PoolType, id=graphene.String(), controller_address=graphene.String())

    async def resolve_pools(self, _info, ordering=None, reversed_order=None):
        pass

    async def resolve_pool(self, _info, id, controller_address):
        pool_type = PoolType(id=id)
        pool_type.controller = ControllerType(address=controller_address)
        return pool_type


class PoolMutations(graphene.ObjectType):
    addStaticPool = AddStaticPool.Field()


pool_schema = graphene.Schema(query=PoolQuery,
                              mutation=PoolMutations,
                              auto_camelcase=False)
