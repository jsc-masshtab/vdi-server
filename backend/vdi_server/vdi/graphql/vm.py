import graphene
from asyncpg.connection import Connection
from vdi.context_utils import enter_context

from .pool import TemplateType, VmType
from .resources import NodeType
from .util import get_selections
from ..db import db
from ..tasks import resources
from ..tasks.vm import ListVms, ListTemplates



class PoolWizardMixin:

    def poolwizard():
        from vdi.graphql.pool import PoolSettings
        return PoolSettings

    poolwizard = graphene.Field(poolwizard, controller_ip=graphene.String(), template_id=graphene.String())

    async def resolve_poolwizard(self, info, controller_ip=None, template_id=None):
        if controller_ip is None:
            from vdi.graphql.resources import get_controller_ip
            controller_ip = await get_controller_ip()
        if template_id is None:
            [template] = await ListTemplates(controller_ip=controller_ip)
            template_id = template['id']
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
                              controller_ip=graphene.String(), cluster_id=graphene.String(), node_id=graphene.String())
    vms = graphene.List(VmType,
                        controller_ip=graphene.String(), cluster_id=graphene.String(), node_id=graphene.String(),
                        include_wild=graphene.Boolean())


    @enter_context(lambda: db.connect())
    async def resolve_templates(conn: Connection, self, info, controller_ip=None, cluster_id=None, node_id=None):
        if controller_ip is None:
            from vdi.graphql.resources import get_controller_ip
            controller_ip = await get_controller_ip()
        if node_id is not None:
            nodes = {node_id}
        elif cluster_id is not None:
            nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
            nodes = {node['id'] for node in nodes}
        else:
            nodes = None
        vms = await ListTemplates(controller_ip=controller_ip)
        if nodes is not None:
            vms = [
                vm for vm in vms
                if vm['node']['id'] in nodes
            ]
        objects = []
        for vm in vms:
            node = NodeType(id=vm['node']['id'], verbose_name=vm['node']['verbose_name'])
            node.controller_ip = controller_ip
            obj = TemplateType(name=vm['verbose_name'], info=vm, id=vm['id'], node=node)
            obj.controller_ip = controller_ip
            objects.append(obj)
        return objects

    async def resolve_vms(self, info, controller_ip=None, cluster_id=None, node_id=None,
                          include_wild=False):
        if controller_ip is None:
            from vdi.graphql.resources import get_controller_ip
            controller_ip = await get_controller_ip()
        if node_id is not None:
            nodes = {node_id}
        elif cluster_id is not None:
            nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
            nodes = {node['id'] for node in nodes}
        else:
            nodes = None
        vms = await ListVms(controller_ip=controller_ip)
        if nodes is not None:
            vms = [
                vm for vm in vms
                if vm['node']['id'] in nodes
            ]
        vm_ids = [vm['id'] for vm in vms]
        if not include_wild:
            async with db.connect() as conn:
                qu = "select id from vm where id = any($1::text[])", vm_ids
                data = await conn.fetch(*qu)
                vm_ids = {item['id'] for item in data}

        objects = []
        for vm in vms:
            if vm['id'] not in vm_ids:
                continue
            node = NodeType(id=vm['node']['id'], verbose_name=vm['node']['verbose_name'])
            node.controller_ip = controller_ip
            obj = VmType(name=vm['verbose_name'], id=vm['id'], node=node)
            obj.selections = get_selections(info)
            obj.info = vm
            obj.controller_ip = controller_ip
            objects.append(obj)
        return objects

