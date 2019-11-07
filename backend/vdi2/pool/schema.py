# -*- coding: utf-8 -*-
import graphene

from common.veil_errors import SimpleError
from common.utils import get_selections

from settings import MIX_POOL_SIZE, MAX_POOL_SIZE, MAX_VM_AMOUNT_IN_POOL, DEFAULT_NAME

from auth.schema import UserType
from auth.models import User

from vm.schema import VmType, VmQuery
from vm.models import Vm
from vm.veil_client import VmHttpClient

from controller.schema import ControllerType

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
    desktop_pool_type = DesktopPoolTypeGraphene()


class PoolSettings(graphene.ObjectType, PoolSettingsFields):
    pass


class PoolType(graphene.ObjectType):

    id = graphene.Int() # wrong type?
    template_id = graphene.String()
    desktop_pool_type = DesktopPoolTypeGraphene()
    name = graphene.String()
    settings = graphene.Field(PoolSettings)
    users = graphene.List(UserType, entitled=graphene.Boolean())
    vms = graphene.List(VmType)
    pool_resources_names = graphene.Field(PoolResourcesNames)
    status = graphene.String()

    controller = ControllerType()

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
            # todo: not sure...
            users_data = await User.outerjoin(PoolUsers, User.id == PoolUsers.user_id).select().where(
                 PoolUsers.pool_id != self.id).gino.all()
        print('users_data', users_data)
        # todo: it will not work until model and grapnene feilds are syncronized
        uset_type_list = [
            UserType(**user.__values__)
            for user in users_data
        ]
        return uset_type_list

    async def resolve_vms(self, _info):
        vm_type_list = []

        vms_data = await Vm.select("id").where((Vm.pool_id == self.id)).gino.all()
        for (vm_id,) in vms_data:
            vm_http_client = await VmHttpClient.create(self.controller.address, vm_id)
            veil_info = await vm_http_client.info()
            # create graphene type
            vm_type = VmQuery.veil_vm_data_to_graphene_type(veil_info, self.controller.address)
            vm_type_list.append(vm_type)

        return vm_type_list

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
        return self.determine_pool_status()

    async def determine_pool_status(self):

        if not self.status:
            # determine pool status. If we cant get veil info about at least one vm
            # we consider the pool as broken
            pass
            # vms = await self._form_vm_type_list(['state'])
            #
            # vms_info_list = [single_vm.veil_info for single_vm in vms]
            # if Unset in vms_info_list:
            #     self.status = 'FAILED'
            # else:
            #     self.status = 'ACTIVE'
        return self.status


class PoolQuery(graphene.ObjectType):
    pools = graphene.List(PoolType, ordering=graphene.String(), reversed_order=graphene.Boolean())
    pool = graphene.Field(PoolType, id=graphene.Int(), controller_ip=graphene.String())

    async def resolve_pools(self, _info, ordering=None, reversed_order=None):
        pass

    async def resolve_pool(self, _info, id):

        pass


class PoolMutations(graphene.ObjectType):
    pass


pool_schema = graphene.Schema(query=PoolQuery,
                              mutation=PoolMutations,
                              auto_camelcase=False)