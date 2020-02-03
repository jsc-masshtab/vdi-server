import graphene
import json
import logging

from tornado.httpclient import HTTPClientError
from graphql import GraphQLError

from settings import DEFAULT_NAME
from common.utils import extract_ordering_data
from common.veil_errors import HttpError, SimpleError
from common.veil_decorators import superuser_required
from vm.models import Vm
from vm.veil_client import VmHttpClient
from pool.models import PoolUsers
from controller_resources.veil_client import ResourcesHttpClient
from controller.models import Controller
from controller.schema import ControllerType
from user.user_schema import UserType
from user.models import User

application_log = logging.getLogger('tornado.application')


class VmState(graphene.Enum):
    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class TemplateType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    veil_info = graphene.String()
    veil_info_json = graphene.String()
    controller = graphene.Field(ControllerType)

    async def resolve_veil_info_json(self, _info):
        return json.dumps(self.veil_info)


class VmType(graphene.ObjectType):
    verbose_name = graphene.String()
    id = graphene.String()
    veil_info = graphene.String()
    veil_info_json = graphene.String()
    template = graphene.Field(TemplateType)
    user = graphene.Field(UserType)
    state = graphene.Field(VmState)
    status = graphene.String()
    controller = graphene.Field(ControllerType)

    management_ip = graphene.String()

    selections = None  # List[str]
    sql_data = None

    async def get_veil_info(self):

        if self.veil_info:
            return

        try:
            vm_client = await VmHttpClient.create(controller_ip=self.controller.address, vm_id=self.id)
            self.veil_info = await vm_client.info()
        except HTTPClientError:
            return

    async def resolve_veil_info_json(self, _info):
        return json.dumps(self.veil_info)

    async def resolve_verbose_name(self, _info):
        if self.verbose_name:
            return self.verbose_name

        await self.get_veil_info()
        if self.veil_info:
            return self.veil_info['verbose_name']
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

        await self.get_veil_info()
        # get template id and name from veil_info
        try:
            template_id = self.veil_info['parent']['id']
            template_name = self.veil_info['parent']['verbose_name']
        except (TypeError, KeyError):
            template_id = None
            template_name = DEFAULT_NAME

        self.template = TemplateType(id=template_id, veil_info=None, verbose_name=template_name)


class AssignVmToUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)
        username = graphene.String(required=True)

    ok = graphene.Boolean()

    @superuser_required
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
        await Vm.update.values(username=None).where(
            (Vm.pool_id == pool_id) & (Vm.username == username)).gino.status()

        # assign vm to the user(username)
        await Vm.attach_vm_to_user(vm_id, username)

        return {
            'ok': True
        }


class FreeVmFromUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, vm_id):
        # check if vm exists
        vm = await Vm.get(vm_id)
        if vm:
            await vm.free_vm()
            return {'ok': True}
        return {'ok': False}


class VmQuery(graphene.ObjectType):
    template = graphene.Field(TemplateType, id=graphene.String(), controller_address=graphene.String())
    vm = graphene.Field(VmType, id=graphene.String(), controller_address=graphene.String())

    templates = graphene.List(TemplateType, controller_ip=graphene.String(), cluster_id=graphene.String(),
                              node_id=graphene.String(), ordering=graphene.String())

    vms = graphene.List(VmType,
                        controller_ip=graphene.String(),
                        cluster_id=graphene.String(),
                        node_id=graphene.String(),
                        datapool_id=graphene.String(),
                        get_vms_in_pools=graphene.Boolean(),
                        ordering=graphene.String())

    @superuser_required
    async def resolve_template(self, _info, id, controller_address):
        application_log.debug('GraphQL: Resolving template info')
        vm_http_client = await VmHttpClient.create(controller_address, id)
        try:
            veil_info = await vm_http_client.info()
        except HttpError as e:
            raise SimpleError('Не удалось получить данные Шаблона: {}'.format(e))

        return VmQuery.veil_template_data_to_graphene_type(veil_info, controller_address)

    @superuser_required
    async def resolve_vm(self, _info, id, controller_address):
        vm_http_client = await VmHttpClient.create(controller_address, id)
        try:
            veil_info = await vm_http_client.info()
        except HttpError as e:
            raise SimpleError('Не удалось получить данные ВМ: {}'.format(e))

        return VmQuery.veil_vm_data_to_graphene_type(veil_info, controller_address)

    @superuser_required
    async def resolve_templates(self, _info, controller_ip=None, cluster_id=None, node_id=None, ordering=None):
        if controller_ip:
            vm_http_client = await VmHttpClient.create(controller_ip, '')
            try:
                template_veil_data_list = await vm_http_client.fetch_templates_list(node_id=node_id)
            except HttpError as e:
                raise SimpleError('Не удалось получить список шаблонов: {}'.format(e))

            template_veil_data_list = await VmQuery.filter_domains_by_cluster(
                template_veil_data_list, controller_ip, cluster_id)

            template_type_list = VmQuery.veil_template_data_to_graphene_type_list(
                template_veil_data_list, controller_ip)
        else:
            controllers_addresses = await Controller.get_controllers_addresses()

            template_type_list = []
            for controller_address in controllers_addresses:
                vm_http_client = await VmHttpClient.create(controller_address, '')
                try:
                    single_template_veil_data_list = await vm_http_client.fetch_templates_list(node_id=node_id)

                    single_template_veil_data_list = await VmQuery.filter_domains_by_cluster(
                        single_template_veil_data_list, controller_address, cluster_id)

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

    @superuser_required
    async def resolve_vms(self, _info, controller_ip=None, cluster_id=None, node_id=None, datapool_id=None,
                          get_vms_in_pools=False, ordering=None):
        application_log.debug('GraphQL: Resolving VMs')
        # get veil vm data list
        if controller_ip:
            vm_http_client = await VmHttpClient.create(controller_ip, '')
            try:
                vm_veil_data_list = await vm_http_client.fetch_vms_list(node_id=node_id, datapool_id=datapool_id)
            except HttpError as e:
                raise SimpleError('Не удалось получить список ВМ: {}'.format(e))

            vm_veil_data_list = await VmQuery.filter_domains_by_cluster(vm_veil_data_list, controller_ip, cluster_id)

            vm_type_list = VmQuery.veil_vm_data_to_graphene_type_list(vm_veil_data_list, controller_ip)
            application_log.debug('GraphQL: VM type list:')

        # if controller address is not provided then take all vms from all controllers
        else:
            controllers_addresses = await Controller.get_controllers_addresses()

            vm_type_list = []
            for controller_address in controllers_addresses:
                vm_http_client = await VmHttpClient.create(controller_address, '')
                try:
                    single_vm_veil_data_list = await vm_http_client.fetch_vms_list(node_id=node_id,
                                                                                   datapool_id=datapool_id)

                    single_vm_veil_data_list = await VmQuery.filter_domains_by_cluster(
                        single_vm_veil_data_list, controller_address, cluster_id)

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

        application_log.debug('vm_type_list_count {}'.format(len(vm_type_list)))
        return vm_type_list

    @staticmethod
    def veil_template_data_to_graphene_type(template_veil_data, controller_address):
        application_log.debug(template_veil_data)
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

    @staticmethod
    async def filter_domains_by_cluster(domains_veil_data_list, controller_ip, cluster_id):
        """filter templates and vms list by cluster"""
        if cluster_id:
            resources_http_client = await ResourcesHttpClient.create(controller_ip)
            node_veil_data_list = await resources_http_client.fetch_node_list(cluster_id=cluster_id)
            nodes_ids = {node['id'] for node in node_veil_data_list}

            domains_veil_data_list = list(filter(lambda domain_data: domain_data['node']['id'] in nodes_ids,
                                                 domains_veil_data_list))

        return domains_veil_data_list


class VmMutations(graphene.ObjectType):
    assignVmToUser = AssignVmToUser.Field()
    freeVmFromUser = FreeVmFromUser.Field()


vm_schema = graphene.Schema(query=VmQuery,
                            mutation=VmMutations,
                            auto_camelcase=False)
