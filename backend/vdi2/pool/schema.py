# -*- coding: utf-8 -*-
import graphene

from common.veil_errors import SimpleError

from settings import MIX_POOL_SIZE, MAX_POOL_SIZE, MAX_VM_AMOUNT_IN_POOL, DEFAULT_NAME

from vdi.errors import SimpleError, FieldError, NotFound, FetchException

from auth.schema import UserType
from vm.schema import VmType
from vdi.graphql_api.resources import ControllerType

from common.utils import get_selections

from pool.models import DesktopPoolType, Pool


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

    id = graphene.Int()
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
        # todo: rewrite in ORM later
        return []
        # u_fields = ('username', 'email', 'date_joined')
        # # users who are entitled to pool
        # if entitled:
        #     u_fields_joined = ', '.join('u.{}'.format(f) for f in u_fields)
        #     async with db.connect() as conn:
        #         qu = """
        #         SELECT {}
        #         FROM pools_users JOIN public.user as u ON pools_users.username = u.username
        #         WHERE pool_id = {}
        #         """.format(u_fields_joined, self.id)
        #         data = await conn.fetch(qu)
        # # users who are NOT entitled to pool
        # else:
        #     u_fields_joined = ', '.join('{}'.format(f) for f in u_fields)
        #     async with db.connect() as conn:
        #         qu = """
        #         SELECT {}
        #         FROM public.user
        #         WHERE public.user.username NOT IN
        #             (SELECT pools_users.username
        #              FROM pools_users
        #              WHERE pools_users.pool_id = {}
        #             )
        #         """.format(u_fields_joined, self.id)
        #         data = await conn.fetch(qu)
        #
        # # form list and return
        # users = []
        # for u in data:
        #     u = dict(zip(u_fields, u))
        #     users.append(UserType(**u))
        # return users

    async def resolve_vms(self, info):
        # todo: return list of vms in this pool
        return []

    def resolve_desktop_pool_type(self, _info):
        if not self.desktop_pool_type:
            # todo: orm query
            pass
        return self.desktop_pool_type

    async def resolve_settings(self, _info):
        if not self.settings:
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
