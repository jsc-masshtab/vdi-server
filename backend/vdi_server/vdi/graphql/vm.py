import graphene

from .util import get_selections
from ..db import db
from ..tasks import resources
from ..tasks.vm import ListTemplates
from ..tasks.resources import DiscoverControllers
from .pool import VmType, TemplateType

from vdi.errors import SimpleError


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