import graphene

from .util import get_selections
from ..db import db
from ..tasks import resources
from ..tasks.vm import ListTemplates
from ..tasks.resources import ListControllers
from .pool import VmType, TemplateType


class AssignVmToUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.String()
        username = graphene.String()

    ok = graphene.Boolean()

    async def mutate(self, _info, vm_id, username):

        async with db.connect() as conn:
            # find pool the vm belongs to
            qu = f'SELECT vm.pool_id from vm WHERE vm.id = $1 ', vm_id
            pool_ids = await conn.fetch(*qu)

            if not pool_ids:
                return {
                    'ok': False,
                    'error': 'Requested vm doesnt belong to any pool'
                }
            else:
                [(pool_id,)] = pool_ids
                print('AssignVmToUser::mutate pool_id', pool_id)

            # check if the user is entitled to pool(pool_id) the vm belongs to
            qu = f'SELECT * from pools_users WHERE pool_id = $1 AND username = $2', pool_id, username
            pools_users_data = await conn.fetch(*qu)
            if not pools_users_data:
                return {
                    'ok': False,
                    'error': 'Requested user is not entitled to the pool the requested vm belong to'
                }

            # another vm in the pool may have this user as owner. Reset ownership
            qu = f'UPDATE vm SET username = NULL WHERE pool_id = $1 AND username = $2', pool_id, username
            await conn.fetch(*qu)

            # assign vm to the user(username)
            qu = "update vm set username = $1 where id = $2", username, vm_id
            await conn.fetch(*qu)

        return {
            'ok': True,
            'error': 'null'
        }

class PoolWizardMixin:

    def poolwizard():
        from vdi.graphql.pool import PoolSettings
        return PoolSettings

    poolwizard = graphene.Field(poolwizard)

    async def resolve_poolwizard(self, info):
        controllers = await ListControllers()
        controller_ip = controllers[0]['ip']
        templates = await ListTemplates(controller_ip=controller_ip)
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