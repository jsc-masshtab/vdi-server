import graphene
import asyncio
import inspect
import json

from tornado.httpclient import HTTPClientError

from cached_property import cached_property as cached

from graphql import GraphQLError

from settings import DEFAULT_NAME
from common.utils import get_selections, make_graphene_type
from common.veil_errors import HttpError, SimpleError, NotFound

from vm.models import Vm
from vm.veil_client import VmHttpClient

from pool.models import PoolUsers

from controller.models import Controller
from controller.schema import ControllerType

from auth.schema import UserType


class VmState(graphene.Enum):
    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class TemplateType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    veil_info = graphene.String(get=graphene.String())
    info = graphene.String(get=graphene.String())

    def resolve_info(self, info, get=None):
        return self.resolve_veil_info(info, get)

    def resolve_veil_info(self, _info, get=None):
        veil_info = self.veil_info
        return veil_info


class VmType(graphene.ObjectType):
    verbose_name = graphene.String()
    id = graphene.String()
    veil_info = graphene.String()
    template = graphene.Field(TemplateType)
    user = graphene.Field(UserType)
    state = graphene.Field(VmState)
    status = graphene.String()
    controller = ControllerType()

    selections = None #List[str]
    sql_data = None

    @cached
    async def cached_veil_info(self):

        if self.veil_info:
            return self.veil_info

        try:
            vm_client = VmHttpClient(controller_ip=self.controller.address, vm_id=self.id)
            vm_info = await vm_client.info()
            return vm_info
        except HTTPClientError:
            return None

    async def resolve_verbose_name(self, info):
        if self.verbose_name:
            return self.verbose_name
        if self.cached_veil_info:
            return self.cached_veil_info['verbose_name']
        else:
            return DEFAULT_NAME

    async def resolve_user(self, _info):
        username = await Vm.get_username(self.id)
        return UserType(username=username)

    async def resolve_template(self, info):
        if self.template:
            return self.template

        template_id = Vm.get_template_id(self.id)

        # get data from veil
        try:
            vm_client = VmHttpClient(controller_ip=self.controller.address, vm_id=template_id)
            template_info = await vm_client.info()
        except NotFound:
            template_info = None

        template_name = template_info['verbose_name'] if template_info else DEFAULT_NAME
        return TemplateType(id=template_id, veil_info=template_info, verbose_name=template_name)

    async def resolve_state(self, _info):
        if self.cached_veil_info:
            val = self.cached_veil_info['user_power_state']
            return VmState.get(val)
        else:
            return VmState.UNDEFINED

    async def resolve_status(self, _info):
        if self.cached_veil_info:
            return self.cached_veil_info['status']
        else:
            return DEFAULT_NAME


class AssignVmToUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)
        username = graphene.String(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, vm_id, username):
        # find pool the vm belongs to
        pool_id = await Vm.get_pool_id(vm_id)
        if not pool_id:
            # Requested vm doesnt belong to any pool
            raise GraphQLError('ВМ не находится ни в одном из пулов')

        # check if the user is entitled to pool(pool_id) the vm belongs to
        row_exists = await PoolUsers.check_row_exists(pool_id, username)
        if not row_exists:
            # Requested user is not entitled to the pool the requested vm belong to
            raise GraphQLError('У пользователя нет прав на использование пула, которому принадлежит ВМ')

        # another vm in the pool may have this user as owner. Remove assignment
        await Vm.free_vm(pool_id, username)

        # assign vm to the user(username)
        await Vm.attach_vm_to_user(vm_id, username)

        return {
            'ok': True
        }


class FreeVmFromUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, vm_id):
        # check if vm exists
        vm_exists = await Vm.check_vm_exists(vm_id)
        if not vm_exists:
            raise GraphQLError('ВМ с заданным id не существует')

        # free vm from user
        await Vm.free_vm(vm_id)

        return {
            'ok': True
        }


class VmQuery(graphene.ObjectType):
    list_of_vms = graphene.List(VmType, controller_ip=graphene.String(), cluster_id=graphene.String(),
                                node_id=graphene.String(), datapool_id=graphene.String(),
                                get_vms_in_pools=graphene.Boolean(),
                                ordering=graphene.String(), reversed_order=graphene.Boolean())

    async def resolve_list_of_vms(self, _info, controller_ip=None, cluster_id=None, node_id=None,
                                  get_vms_in_pools=False, ordering=None, reversed_order=None):

        # get veil vm data list
        if controller_ip:
            vm_http_client = VmHttpClient(controller_ip, '')
            vm_veil_data_list = await vm_http_client.fetch_vms_list(cluster_id=cluster_id, node_id=node_id)
            vm_type_list = VmQuery.veil_vm_data_to_graphene_type_list(vm_veil_data_list)

        # if controller address is not provided then take all vms from all controllers
        else:
            controllers_addresses = await Controller.get_controllers_addresses()

            vm_type_list = []
            for controller_address in controllers_addresses:
                vm_http_client = VmHttpClient(controller_ip=controller_address)
                try:
                    single_vm_veil_data_list = await vm_http_client.fetch_vms_list()
                    single_vm_type_list = VmQuery.veil_vm_data_to_graphene_type_list(single_vm_veil_data_list)
                    vm_type_list.append(single_vm_type_list)
                except (HttpError, OSError):
                    pass

        # if get_vms_in_pools is True then take all existing vms
        # if get_vms_in_pools is False then take only that vms which are not in any pools
        # flag get_vms_in_pools is very important for static pools' creation
        if not get_vms_in_pools:
            # get all vms ids which are in pools
            vm_ids_in_pools = await Vm.get_all_vms_ids()
            # filter
            vm_type_list = list(filter(lambda vm_type: vm_type.id not in vm_ids_in_pools, vm_type_list))

        # sorting
        if ordering:
            if ordering == 'name':
                def sort_lam(vm_type):
                    return vm_type.name if vm_type.name else DEFAULT_NAME
            elif ordering == 'node':
                for vm_type in vm_type_list:
                    await vm_type.node.determine_management_ip()

                def sort_lam(vm_type):
                    return vm_type.node.management_ip if vm_type.node.management_ip else DEFAULT_NAME
            elif ordering == 'template':
                def sort_lam(vm_type):
                    print('vm_type.template.name', vm_type.template.name)
                    return vm_type.template.name if vm_type.template else DEFAULT_NAME
            elif ordering == 'status':
                def sort_lam(vm_type):
                    return vm_type.status if vm_type and vm_type.status else DEFAULT_NAME
            else:
                raise SimpleError('Неверный параметр сортировки')
            reverse = reversed_order if reversed_order is not None else False
            vm_type_list = sorted(vm_type_list, key=sort_lam, reverse=reverse)

        return vm_type_list

    @staticmethod
    def veil_vm_data_to_graphene_type(vm_veil_data, controller_address):
        vm_type = VmType(id=vm_veil_data['id'], verbose_name=vm_veil_data['verbose_name'])
        vm_type.veil_info = vm_veil_data
        vm_type.controller = ControllerType(address=controller_address)
        return vm_type

    @staticmethod
    def veil_vm_data_to_graphene_type_list(vm_veil_data_list, controller_address):
        vm_type_list = []
        for vm_veil_data in vm_veil_data_list:
            vm_type = VmQuery.veil_vm_data_to_graphene_type(vm_veil_data, controller_address)
            vm_type_list.append(vm_type)
        return vm_type_list


class VmMutations(graphene.ObjectType):
    assignVmToUser = AssignVmToUser.Field()
    freeVmFromUser = FreeVmFromUser.Field()


vm_schema = graphene.Schema(query=VmQuery,
                            mutation=VmMutations,
                            auto_camelcase=False)
