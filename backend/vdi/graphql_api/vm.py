import graphene

from .util import get_selections
from db.db import db
from ..tasks import resources
from ..tasks.vm import ListTemplates
from ..tasks.vm import ListVms
from ..tasks.resources import DiscoverControllers
from .pool import VmType, TemplateType

from vdi.tasks.resources import DiscoverControllerIp
from vdi.graphql_api.resources import NodeType, ControllerType
from vdi.constants import DEFAULT_NAME

#from vdi.utils import print
from vdi.errors import SimpleError, FieldError


class AssignVmToUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)
        username = graphene.String(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, vm_id, username):
        async with db.connect() as conn:
            # find pool the vm belongs to
            qu = 'SELECT vm.pool_id from vm WHERE vm.id = $1 ', vm_id
            pool_ids = await conn.fetch(*qu)

            if not pool_ids:
                # Requested vm doesnt belong to any pool
                raise SimpleError('ВМ не находится ни в одном из пулов')
            else:
                [(pool_id,)] = pool_ids
                print('AssignVmToUser::mutate pool_id', pool_id)

            # check if the user is entitled to pool(pool_id) the vm belongs to
            qu = 'SELECT * from pools_users WHERE pool_id = $1 AND username = $2', pool_id, username
            pools_users_data = await conn.fetch(*qu)
            if not pools_users_data:
                # Requested user is not entitled to the pool the requested vm belong to
                raise SimpleError('У пользователя нет прав на использование пула, которому принадлежит ВМ')

            # another vm in the pool may have this user as owner. Remove assignment
            qu = 'UPDATE vm SET username = NULL WHERE pool_id = $1 AND username = $2', pool_id, username
            await conn.fetch(*qu)

            # assign vm to the user(username)
            qu = "update vm set username = $1 where id = $2", username, vm_id
            await conn.fetch(*qu)

        return {
            'ok': True
        }


class FreeVmFromUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, vm_id):
        async with db.connect() as conn:
            # check if vm exists
            qu = 'SELECT * from vm WHERE id = $1', vm_id
            vm_data = await conn.fetch(*qu)
            if not vm_data:
                raise SimpleError('ВМ с заданным id не существует')
            # free vm from user
            qu = 'UPDATE vm SET username = NULL WHERE id = $1', vm_id
            await conn.fetch(*qu)

        return {
            'ok': True
        }


class PoolWizardMixin:

    def poolwizard():
        from vdi.graphql_api.pool import PoolSettings
        return PoolSettings

    poolwizard = graphene.Field(poolwizard)

    async def resolve_poolwizard(self, info):
        connected, broken = await DiscoverControllers(return_broken=True)
        if not connected:
            if broken:
                raise SimpleError("Отсутствует подключение к контроллерам")
            raise SimpleError("Нет добавленных контроллеров")
        controller_ip = connected[0]['ip']
        templates = await ListTemplates(controller_ip=controller_ip)
        if not templates:
            raise SimpleError("Нет шаблонов")
        template_id = templates[0]['id']

        from vdi.tasks.vm import GetDomainInfo
        from vdi.tasks.resources import FetchNode
        settings = {}
        selections = get_selections(info)
        if any(key in selections
               for key in ['node_id', 'cluster_id', 'datapool_id']):
            template = await GetDomainInfo(controller_ip=controller_ip, domain_id=template_id)
            node_id = settings['node_id'] = template['node']['id']
        if 'datapool_id' in selections:
            datapools = await resources.ListDatapools(controller_ip=controller_ip, node_id=node_id)
            if not datapools:
                raise SimpleError("На сервере нет датапулов")
            settings['datapool_id'] = datapools[0]['id']
        if 'cluster_id' in selections:
            node = await FetchNode(controller_ip=controller_ip, node_id=node_id)
            settings['cluster_id'] = node['cluster']['id']
        from vdi.settings import settings as global_settings
        from vdi.graphql_api.pool import PoolSettings
        return PoolSettings(**settings, **{
            #'controller_ip': controller_ip,
            'template_id': template_id,
            'initial_size': global_settings['pool']['initial_size'],
            'reserve_size': global_settings['pool']['reserve_size'],
        })

    # async def resolve_list_of_vms(self, _info, cluster_id, node_id, datapool_id='', get_vms_in_pools=False,
    #                               ordering=None, reversed_order=None):

# get list of vms from veil
class ListOfVmsQuery:
    list_of_vms = graphene.List(VmType, cluster_id=graphene.String(),
        node_id=graphene.String(), datapool_id=graphene.String(), get_vms_in_pools=graphene.Boolean(),
                                ordering=graphene.String(), reversed_order=graphene.Boolean())

    async def resolve_list_of_vms(self, _info, cluster_id=None, node_id=None, datapool_id='', get_vms_in_pools=False,
                                  ordering=None, reversed_order=None):

        print('ListOfVmsQuery::resolve_vms_on_veil: datapool_id', datapool_id)

        # get all vms ids which are in pools
        vm_ids_in_pools = await ListOfVmsQuery.get_all_vms_ids_in_pools()

        if cluster_id and node_id:
            # get all vms from veil
            controller_ip = await DiscoverControllerIp(cluster_id=cluster_id, node_id=node_id)
            all_vms = await ListVms(controller_ip=controller_ip)

            # create list of filtered vm
            if get_vms_in_pools:  # get all vms on node
                all_vms = [vm for vm in all_vms if vm['node']['id'] == node_id]
            else:  # get only free vms (not in pools)
                all_vms = [vm for vm in all_vms if not ListOfVmsQuery.check_if_vm_in_pool(vm, vm_ids_in_pools) and
                           vm['node']['id'] == node_id]

            # veil vm data to vm_type list
            controller_type = ControllerType(ip=controller_ip)
            vm_type_list = []
            for vm in all_vms:
                node = NodeType(id=node_id, controller=controller_type)
                vm_type = VmType(id=vm['id'], name=vm['verbose_name'], node=node)
                vm_type_list.append(vm_type)

        # if cluster_id and node_id are not defined then take all vms from all controllers
        elif not cluster_id and not node_id:
            controllers = await DiscoverControllers(return_broken=False)
            vm_type_list = []
            for controller in controllers:
                controller_type = ControllerType(ip=controller['ip'])

                vms_veil_data = await ListVms(controller_ip=controller['ip'])
                #print('vms_veil_data', vms_veil_data)
                for vm_veil_data in vms_veil_data:
                    node = NodeType(id=vm_veil_data['node']['id'], controller=controller_type)
                    vm_type = VmType(id=vm_veil_data['id'], name=vm_veil_data['verbose_name'], node=node)
                    vm_type_list.append(vm_type)
                    #print('vm_type.veil_info', vm_type.veil_info)
        else:
            raise SimpleError('cluster_id и node_id должны быть либо оба одновременно указаны, либо оба не указаны')

        # sorting
        if ordering:
            if ordering == 'name':
                def sort_lam(vm_type):
                    return vm_type.name if vm_type.name else DEFAULT_NAME
            elif ordering == 'node':
                for vm_type in vm_type_list:
                    await vm_type.node.determine_management_ip()
                def sort_lam(vm_type):
                    #print('vm_type.node.management_ip', vm_type.node.management_ip)
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
    async def get_all_vms_ids_in_pools():
        async with db.connect() as conn:
            qu = 'SELECT id FROM vm'
            vm_ids_in_pools = await conn.fetch(qu)
        print('ListOfVmsQuery::resolve_vms_on_veil: vm_ids_in_pool', vm_ids_in_pools)
        return vm_ids_in_pools

    @staticmethod
    def check_if_vm_in_pool(vm, vm_ids_in_pools):
        for vm_id in vm_ids_in_pools:
            [(id_str)] = vm_id
            if id_str == vm['id']:
                return True
        else:
            return False