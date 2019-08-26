import graphene

from .util import get_selections
from ..db import db
from ..tasks import resources
from ..tasks.vm import ListTemplates
from ..tasks.vm import ListVms
from ..tasks.resources import DiscoverControllers
from .pool import VmType, TemplateType

from vdi.tasks.resources import DiscoverControllerIp
from vdi.graphql.resources import NodeType, ControllerType


from vdi.utils import print
from vdi.errors import SimpleError, FieldError



class AssignVmToUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)
        username = graphene.String(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, vm_id, username):
        async with db.connect() as conn:
            # find pool the vm belongs to
            qu = f'SELECT vm.pool_id from vm WHERE vm.id = $1 ', vm_id
            pool_ids = await conn.fetch(*qu)

            if not pool_ids:
                # Requested vm doesnt belong to any pool
                raise FieldError(vm_id=['ВМ не находится ни в одном из пулов'])
            else:
                [(pool_id,)] = pool_ids
                print('AssignVmToUser::mutate pool_id', pool_id)

            # check if the user is entitled to pool(pool_id) the vm belongs to
            qu = f'SELECT * from pools_users WHERE pool_id = $1 AND username = $2', pool_id, username
            pools_users_data = await conn.fetch(*qu)
            if not pools_users_data:
                # Requested user is not entitled to the pool the requested vm belong to
                raise FieldError(vm_id=['У пользователя нет прав на использование пула, которому принадлежит ВМ'])

            # another vm in the pool may have this user as owner. Remove assignment
            qu = f'UPDATE vm SET username = NULL WHERE pool_id = $1 AND username = $2', pool_id, username
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
            qu = f'SELECT * from vm WHERE id = $1', vm_id
            vm_data = await conn.fetch(*qu)
            if not vm_data:
                raise FieldError(vm_id=['ВМ с заданным id не существует'])
            # free vm from user
            qu = f'UPDATE vm SET username = NULL WHERE id = $1', vm_id
            await conn.fetch(*qu)

        return {
            'ok': True
        }


class PoolWizardMixin:

    def poolwizard():
        from vdi.graphql.pool import PoolSettings
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
            settings['datapool_id'] = datapools[0]['id']
        if 'cluster_id' in selections:
            node = await FetchNode(controller_ip=controller_ip, node_id=node_id)
            settings['cluster_id'] = node['cluster']['id']
        from vdi.settings import settings as global_settings
        from vdi.graphql.pool import PoolSettings
        return PoolSettings(**settings, **{
            'controller_ip': controller_ip,
            'template_id': template_id,
            'initial_size': global_settings['pool']['initial_size'],
            'reserve_size': global_settings['pool']['reserve_size'],
        })


# get list of vms from veil
class ListOfVmsQuery:
    list_of_vms = graphene.List(VmType, cluster_id=graphene.String(),
        node_id=graphene.String(), datapool_id=graphene.String(), get_vms_in_pools=graphene.Boolean())

    async def resolve_list_of_vms(self, _info, cluster_id, node_id, datapool_id, get_vms_in_pools=False):

        print('ListOfVmsQuery::resolve_vms_on_veil: datapool_id', datapool_id)
        # get all vm which are in pools
        async with db.connect() as conn:
            qu = f'select id from vm'
            vm_ids_in_pools = await conn.fetch(qu)
        print('ListOfVmsQuery::resolve_vms_on_veil: vm_ids_in_pool', vm_ids_in_pools)

        # get all vms from veil
        controller_ip = await DiscoverControllerIp(cluster_id=cluster_id, node_id=node_id)
        print('ListOfVmsQuery::resolve_vms_on_veil: controller_ip', controller_ip)
        all_vms = await ListVms(controller_ip=controller_ip)
        breakpoint()
        print('ListOfVmsQuery::resolve_vms_on_veil: all_vms', all_vms)

        # create list of filtered vm
        def check_if_vm_in_pool(vm):
            for vm_id in vm_ids_in_pools:
                [(id_str)] = vm_id
                if id_str == vm['id']:
                    return True
            else:
                return False

        if get_vms_in_pools:  # get all vms on node
            filtered_vms = [vm for vm in all_vms if vm['node']['id'] == node_id]
        else:  # get only free vms (not in pools)
            filtered_vms = [vm for vm in all_vms
                            if not check_if_vm_in_pool(vm) and vm['node']['id'] == node_id
                            ]

        controller = ControllerType(ip=controller_ip)

        vm_type_list = []
        for vm in filtered_vms:
            node = NodeType(id=node_id, controller=controller)
            obj = VmType(id=vm['id'], name=vm['verbose_name'], node=node)
            vm_type_list.append(obj)

        return vm_type_list
