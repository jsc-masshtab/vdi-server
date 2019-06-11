import graphene
import json

import random

from asyncpg.connection import Connection

from ..db import db
from ..tasks import admin, resources
from ..tasks.vm import SetupDomain, DropDomain, ListVms, GetDomainInfo

from .util import get_selections
from .pool import PoolSettings, TemplateType, VmType
from .resources import NodeType, get_controller_ip


from vdi.context_utils import enter_context


class CreateTemplate(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        image_name = graphene.String()

    template = graphene.Field(TemplateType)
    poolwizard = settings = graphene.Field(PoolSettings, format=graphene.String())

    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info, image_name, format='one'):
        from vdi.tasks import admin
        res = await admin.discover_resources(combine=True)
        resource = random.choice(res)
        #FIXME image_name
        domain = await SetupDomain(image_name=image_name, controller_ip=resource['controller_ip'],
                                      node_id=resource['node'], datapool_id=resource['datapool'])
        veil_info = json.dumps(domain)
        qu = "INSERT INTO template_vm (id, veil_info) VALUES ($1, $2)", domain['id'], veil_info
        await conn.fetch(*qu)
        t = TemplateType(id=domain['id'], info=veil_info, name=domain['verbose_name'])
        from vdi.settings import settings
        resources = PoolSettings(**{
            'controller_ip': resource['controller_ip'],
            'cluster_id': resource['cluster'],
            'datapool_id': resource['datapool'],
            'template_id': domain['id'],
            'node_id': resource['node'],
            'initial_size': settings['pool']['initial_size'],
            'reserve_size': settings['pool']['reserve_size'],
        })
        return CreateTemplate(template=t, poolwizard=resources)
        # return CreateTemplate(template=t)


class DropTemplate(graphene.Mutation):
    class Arguments:
        id = graphene.String()
        controller_ip = graphene.String()

    ok = graphene.Boolean()

    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info, id, controller_ip=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        await DropDomain(id=id, controller_ip=controller_ip)
        qu = "DELETE from template_vm WHERE id = $1", id
        await conn.fetch(*qu)
        return DropTemplate(ok=True)



class AddTemplate(graphene.Mutation):
    class Arguments:
        controller_ip = graphene.String()
        id = graphene.String()

    ok = graphene.Boolean()
    poolwizard = graphene.Field(PoolSettings, format=graphene.String())

    async def resolve_poolwizard(self, info):
        from vdi.tasks.vm import GetDomainInfo
        from vdi.tasks.resources import FetchNode
        settings = {}
        selections = get_selections(info)
        if any(key in selections
               for key in ['node_id', 'cluster_id', 'datapool_id']):
            template = await GetDomainInfo(controller_ip=self.controller_ip, domain_id=self.id)
            node_id = settings['node_id'] = template['node']['id']
        if 'datapool_id' in selections:
            datapools = await resources.ListDatapools(controller_ip=self.controller_ip, node_id=node_id)
            settings['datapool_id'] = datapools[0]['id']
        if 'cluster_id' in selections:
            node = await FetchNode(controller_ip=self.controller_ip, node_id=node_id)
            settings['cluster_id'] = node['cluster']['id']
        from vdi.settings import settings as global_settings
        return PoolSettings(**settings, **{
            'controller_ip': self.controller_ip,
            'template_id': self.id,
            'initial_size': global_settings['pool']['initial_size'],
            'reserve_size': global_settings['pool']['reserve_size'],
        })



    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info, id, controller_ip=None):
        if controller_ip is None:
            from vdi.graphql.resources import get_controller_ip
            controller_ip = await get_controller_ip()
        from vdi.tasks import Token, HttpClient
        url = f"http://{controller_ip}/api/domains/{id}/"
        token = await Token(controller_ip=controller_ip)
        headers = {
            'Authorization': f'jwt {token}',
        }
        info = await HttpClient().fetch(url, headers=headers)
        qu = "INSERT INTO template_vm (id, veil_info) VALUES ($1, $2) ON CONFLICT DO NOTHING", id, json.dumps(info)
        await conn.fetch(*qu)
        ret = AddTemplate(ok=True)
        ret.id = id
        ret.controller_ip = controller_ip
        return ret



class TemplateMixin:

    templates = graphene.List(TemplateType,
                              controller_ip=graphene.String(), cluster_id=graphene.String(), node_id=graphene.String())
    vms = graphene.List(VmType,
                        controller_ip=graphene.String(), cluster_id=graphene.String(), node_id=graphene.String())


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
        vms = await ListVms(controller_ip=controller_ip)
        if nodes is not None:
            vms = [
                vm for vm in vms
                if vm['node']['id'] in nodes
            ]

        qu = f"SELECT id FROM template_vm"
        data = await conn.fetch(qu)
        vm_ids = {row['id'] for row in data}
        objects = []
        for vm in vms:
            if vm['id'] not in vm_ids:
                continue
            node = NodeType(id=vm['node']['id'], verbose_name=vm['node']['verbose_name'])
            node.controller_ip = controller_ip
            obj = TemplateType(name=vm['verbose_name'], info=vm, id=vm['id'], node=node)
            obj.controller_ip = controller_ip
            objects.append(obj)
        return objects

    @enter_context(lambda: db.connect())
    async def resolve_vms(conn: Connection, self, info, controller_ip=None, cluster_id=None, node_id=None):
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

        # Filter out templates
        # temporary measure, since veil should know itself, whether a vm is a template
        qu = f"SELECT id FROM template_vm"
        data = await conn.fetch(qu)
        templates_id = {t['id'] for t in data}

        objects = []
        for vm in vms:
            if vm['id'] in templates_id:
                continue
            node = NodeType(id=vm['node']['id'], verbose_name=vm['node']['verbose_name'])
            node.controller_ip = controller_ip
            obj = VmType(name=vm['verbose_name'], id=vm['id'], node=node)
            obj.info = vm
            obj.controller_ip = controller_ip
            objects.append(obj)
        return objects

