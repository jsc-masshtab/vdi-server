import graphene

from .util import get_selections
from ..db import db
from ..tasks import resources
from ..tasks.vm import ListTemplates
from ..tasks.resources import ListControllers
from .pool import VmType, TemplateType


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


class TemplateMixin:
    templates = graphene.List(TemplateType,
                              cluster_id=graphene.String(), node_id=graphene.String())
    vms = graphene.List(VmType,
                        cluster_id=graphene.String(), node_id=graphene.String(),
                        wild=graphene.Boolean())

    async def resolve_templates(self, info, cluster_id=None, node_id=None):
        controller_ip = await resources.DiscoverController(cluster_id=cluster_id, node_id=node_id)
        if controller_ip is None:
            raise resources.NoControllers
        from .resources import ControllerType
        co = ControllerType(ip=controller_ip)
        return await co.resolve_templates(info, cluster_id=cluster_id, node_id=node_id)

    async def resolve_vms(self, info, cluster_id=None, node_id=None, **kwargs):
        # FIXME Token
        controller_ip = await resources.DiscoverController(cluster_id=cluster_id, node_id=node_id)

        if controller_ip is None:
            raise resources.NoControllers
        from .resources import ControllerType
        co = ControllerType(ip=controller_ip)
        return await co.resolve_vms(info, cluster_id=cluster_id, node_id=node_id, **kwargs)


