import graphene
import asyncio
import inspect
import json

from tornado.httpclient import HTTPClientError

from cached_property import cached_property as cached

from graphql import GraphQLError

from common.utils import get_selections, make_graphene_type

from vdi.constants import DEFAULT_NAME
from vdi.errors import NotFound

from vm.veil_client import VmHttpClient
from vm.veil_client import VmHttpClient
from vm.models import Vm

from pool.models import PoolUsers

from auth.schema import UserType


class VmState(graphene.Enum):
    UNDEFINED = 0
    OFF = 1
    SUSPENDED = 2
    ON = 3


class TemplateType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    veil_info = graphene.String(get=graphene.String())
    info = graphene.String(get=graphene.String())

    def resolve_info(self, info, get=None):
        return self.resolve_veil_info(info, get)

    def resolve_veil_info(self, _info, get=None):
        veil_info = self.veil_info
        return veil_info


class VmType(graphene.ObjectType):
    name = graphene.String()
    id = graphene.String()
    veil_info = graphene.String()
    template = graphene.Field(TemplateType)
    user = graphene.Field(UserType)
    state = graphene.Field(VmState)
    status = graphene.String()

    selections = None #List[str]
    sql_data = None
    veil_info = None

    # @cached
    # def controller_ip(self):
    #     return self.pool.controller.ip

    @cached
    async def cached_veil_info(self):
        try:
            vm_client = VmHttpClient(controller_ip=self.controller_ip, domain_id=self.id)
            vm_info = await vm_client.info()
            return vm_info
        except HTTPClientError:
            return None

    # @graphene.Field
    # def node():
    #     from vdi.graphql_api.resources import NodeType
    #     return NodeType

    async def resolve_name(self, info):
        if self.name:
            return self.name
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
            vm_client = VmHttpClient(controller_ip=self.controller_ip, domain_id=template_id)
            template_info = await vm_client.info()
        except NotFound:
            template_info = None

        template_name = template_info['verbose_name'] if template_info else DEFAULT_NAME
        return TemplateType(id=template_id, veil_info=template_info, name=template_name)

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
        Vm.attach_vm_to_user(vm_id, username)

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
