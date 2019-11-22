import graphene
import asyncio
import inspect
import json

from tornado.httpclient import HTTPClientError

from cached_property import cached_property as cached

from graphql import GraphQLError

from settings import DEFAULT_NAME
from common.utils import get_selections, make_graphene_type, extract_ordering_data
from common.veil_errors import HttpError, SimpleError, NotFound

from vm.models import Vm
from vm.veil_client import VmHttpClient

from pool.models import PoolUsers

from controller_resources.veil_client import ResourcesHttpClient
from controller.models import Controller
from controller.schema import ControllerType

from auth.schema import UserType
from auth.models import User


class VmState(graphene.Enum):
    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class TemplateType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    veil_info = graphene.String(get=graphene.String())
    controller = graphene.Field(ControllerType)


class VmType(graphene.ObjectType):
    verbose_name = graphene.String()
    id = graphene.String()
    veil_info = graphene.String()
    template = graphene.Field(TemplateType)
    user = graphene.Field(UserType)
    state = graphene.Field(VmState)
    status = graphene.String()
    controller = graphene.Field(ControllerType)

    management_ip = graphene.String()

    selections = None #List[str]
    sql_data = None

    async def get_veil_info(self):

        if self.veil_info:
            return

        try:
            vm_client = await VmHttpClient.create(controller_ip=self.controller.address, vm_id=self.id)
            self.veil_info = await vm_client.info()
        except HTTPClientError:
            return

    async def resolve_verbose_name(self, _info):
        if self.verbose_name:
            return self.verbose_name

        await self.get_veil_info()
        if self.veil_info:
            return self.veil_info['verbose_name']
        else:
            return DEFAULT_NAME

    async def resolve_user(self, _info):
        username = await Vm.get_username(self.id)
        return UserType(username=username)

    async def resolve_template(self, _info):
        await self.determine_template()
        return self.template

    async def resolve_state(self, _info):
        await self.get_veil_info()
        if self.veil_info:
            val = self.veil_info['user_power_state']
            return VmState.get(val)
        else:
            return VmState.UNDEFINED

    async def resolve_status(self, _info):
        await self.determine_status()
        return self.status

    async def determine_status(self):
        await self.get_veil_info()
        if self.veil_info:
            self.status = self.veil_info['status']
        else:
            self.status = DEFAULT_NAME

    async def resolve_management_ip(self, _info):
        await self.determine_management_ip()
        return self.management_ip

    async def determine_status(self):
        await self.get_veil_info()
        if self.veil_info:
            self.status = self.veil_info['status']
        else:
            self.status = DEFAULT_NAME

    async def determine_management_ip(self):
        if self.management_ip:
            return

        await self.get_veil_info()
        if self.veil_info:
            node_id = self.veil_info['node']['id']
            resources_http_client = await ResourcesHttpClient.create(self.controller.address)
            node_data = await resources_http_client.fetch_node(node_id)
            self.management_ip = node_data['management_ip']

    async def determine_template(self):
        if self.template:
            return

        template_id = await Vm.get_template_id(self.id)

        # get data from veil
        try:
            vm_client = await VmHttpClient.create(controller_ip=self.controller.address, vm_id=template_id)
            template_info = await vm_client.info()
        except NotFound:
            template_info = None

        template_name = template_info['verbose_name'] if template_info else DEFAULT_NAME
        self.template = TemplateType(id=template_id, veil_info=template_info, verbose_name=template_name)


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
        user_id = await User.get_id(username)
        row_exists = await PoolUsers.check_row_exists(pool_id, user_id)
        if not row_exists:
            # Requested user is not entitled to the pool the requested vm belongs to
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
    template = graphene.Field(TemplateType, id=graphene.String(), controller_address=graphene.String())
    vm = graphene.Field(VmType, id=graphene.String(), controller_address=graphene.String())

    templates = graphene.List(TemplateType, controller_ip=graphene.String(), cluster_id=graphene.String(),
                              node_id=graphene.String(), ordering=graphene.String())

    vms = graphene.List(VmType, controller_ip=graphene.String(), cluster_id=graphene.String(),
                                node_id=graphene.String(), datapool_id=graphene.String(),
                                get_vms_in_pools=graphene.Boolean(),
                                ordering=graphene.String())

    async def resolve_template(self, _info, id, controller_address):
        vm_http_client = await VmHttpClient.create(controller_address, id)
        veil_info = await vm_http_client.info()
        return VmQuery.veil_template_data_to_graphene_type(veil_info, controller_address)

    async def resolve_vm(self, _info, id, controller_address):
        vm_http_client = await VmHttpClient.create(controller_address, id)
        veil_info = await vm_http_client.info()
        return VmQuery.veil_vm_data_to_graphene_type(veil_info, controller_address)

    async def resolve_templates(self, _info, controller_ip=None, cluster_id=None, node_id=None, ordering=None):
        if controller_ip:
            vm_http_client = await VmHttpClient.create(controller_ip, '')
            template_veil_data_list = await vm_http_client.fetch_templates_list(cluster_id=cluster_id, node_id=node_id)

            template_type_list = VmQuery.veil_template_data_to_graphene_type_list(
                template_veil_data_list, controller_ip)
        else:
            controllers_addresses = await Controller.get_controllers_addresses()

            template_type_list = []
            for controller_address in controllers_addresses:
                vm_http_client = await VmHttpClient.create(controller_address, '')
                try:
                    single_template_veil_data_list = await vm_http_client.fetch_templates_list()
                    single_template_type_list = VmQuery.veil_template_data_to_graphene_type_list(
                        single_template_veil_data_list, controller_address)
                    template_type_list.extend(single_template_type_list)
                except (HttpError, OSError):
                    pass

        # sorting
        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)

            if ordering == 'verbose_name':
                def sort_lam(template_type):
                    return template_type.verbose_name if template_type.verbose_name else DEFAULT_NAME
            elif ordering == 'controller':
                def sort_lam(template_type):
                    return template_type.controller.address if template_type.controller.address else DEFAULT_NAME
            else:
                raise SimpleError('Неверный параметр сортировки')
            template_type_list = sorted(template_type_list, key=sort_lam, reverse=reverse)

        return template_type_list

    async def resolve_vms(self, _info, controller_ip=None, cluster_id=None, node_id=None, datapool_id=None,
                          get_vms_in_pools=False, ordering=None):

        # get veil vm data list
        if controller_ip:
            vm_http_client = await VmHttpClient.create(controller_ip, '')
            vm_veil_data_list = await vm_http_client.fetch_vms_list(cluster_id=cluster_id, node_id=node_id)
            vm_type_list = VmQuery.veil_vm_data_to_graphene_type_list(vm_veil_data_list, controller_ip)

        # if controller address is not provided then take all vms from all controllers
        else:
            controllers_addresses = await Controller.get_controllers_addresses()

            vm_type_list = []
            for controller_address in controllers_addresses:
                vm_http_client = await VmHttpClient.create(controller_address, '')
                try:
                    single_vm_veil_data_list = await vm_http_client.fetch_vms_list()
                    single_vm_type_list = VmQuery.veil_vm_data_to_graphene_type_list(
                        single_vm_veil_data_list, controller_address)
                    vm_type_list.extend(single_vm_type_list)
                except (HttpError, OSError):
                    pass

        # if get_vms_in_pools is True then take all existing vms
        # if get_vms_in_pools is False then take only that vms which are not in any pools
        # flag get_vms_in_pools is very important for static pools' creation
        if not get_vms_in_pools:
            # get all vms ids which are in pools
            vm_ids_in_pools = await Vm.get_all_vms_ids()
            vm_ids_in_pools = [str(vm_id) for vm_id in vm_ids_in_pools]
            # filter
            vm_type_list = list(filter(lambda vm_type: vm_type.id not in vm_ids_in_pools, vm_type_list))

        # sorting
        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)

            if ordering == 'verbose_name':
                def sort_lam(vm_type):
                    return vm_type.verbose_name if vm_type.verbose_name else DEFAULT_NAME
            elif ordering == 'node':
                for vm_type in vm_type_list:
                    await vm_type.determine_management_ip()

                def sort_lam(vm_type):
                    return vm_type.management_ip if vm_type.management_ip else DEFAULT_NAME
            elif ordering == 'template':
                for vm_type in vm_type_list:
                    await vm_type.determine_template()

                def sort_lam(vm_type):
                    return vm_type.template.verbose_name if vm_type.template else DEFAULT_NAME
            elif ordering == 'status':
                for vm_type in vm_type_list:
                    await vm_type.determine_status()

                def sort_lam(vm_type):
                    return vm_type.status if vm_type and vm_type.status else DEFAULT_NAME
            else:
                raise SimpleError('Неверный параметр сортировки')
            vm_type_list = sorted(vm_type_list, key=sort_lam, reverse=reverse)

        return vm_type_list

    @staticmethod
    def veil_template_data_to_graphene_type(template_veil_data, controller_address):
        template_type = TemplateType(id=template_veil_data['id'], verbose_name=template_veil_data['verbose_name'],
                                     veil_info=template_veil_data)
        template_type.controller = ControllerType(address=controller_address)
        return template_type

    @staticmethod
    def veil_template_data_to_graphene_type_list(template_veil_data_list, controller_address):
        template_veil_data_list_type_list = []
        for template_veil_data in template_veil_data_list:
            template_type = VmQuery.veil_template_data_to_graphene_type(template_veil_data, controller_address)
            template_veil_data_list_type_list.append(template_type)
        return template_veil_data_list_type_list

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
