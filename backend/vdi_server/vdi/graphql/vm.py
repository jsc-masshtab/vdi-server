import graphene
import json

import random

from asyncpg.connection import Connection

from ..db import db
from ..tasks import admin, resources
from ..tasks.vm import SetupDomain, DropDomain, ListVms

from .util import get_selections
from .pool import PoolSettings, TemplateType, VmType
from .resources import NodeType


from vdi.context_utils import enter_context


class CreateTemplate(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        image_name = graphene.String()

    template = graphene.Field(TemplateType)
    poolwizard = settings = graphene.Field(PoolSettings, format=graphene.String())
    resources = 1

    # Output = CreateTemplateOutput

    async def resolve_resources(self, info):
        raise NotImplementedError
        breakpoint()

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

    ok = graphene.Boolean()

    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info, id):
        await DropDomain(id=id)
        qu = "DELETE from template_vm WHERE id = $1", id
        await conn.fetch(*qu)
        return DropTemplate(ok=True)



class AddTemplate(graphene.Mutation):
    class Arguments:
        controller_ip = graphene.String()
        id = graphene.String()

    ok = graphene.Boolean()

    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info, id, controller_ip=None):
        if controller_ip is None:
            from vdi.graphql.resources import get_controller_ip
            controller_ip = await get_controller_ip()
        from vdi.tasks import Token, HttpClient
        url = f"http://{controller_ip}/api/domains/{id}/"
        headers = {
            'Authorization': f'jwt {await Token()}',
        }
        info = await HttpClient().fetch(url, headers=headers)
        qu = "INSERT INTO template_vm (id, veil_info) VALUES ($1, $2)", id, json.dumps(info)
        await conn.fetch(*qu)
        return AddTemplate(ok=True)



class TemplateMixin:

    templates = graphene.List(TemplateType,
                              controller_ip=graphene.String(), cluster_id=graphene.String(), node_id=graphene.String())
    vms = graphene.List(TemplateType,
                        controller_ip=graphene.String(), cluster_id=graphene.String(), node_id=graphene.String())


    #FIXME!!!!
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
        vms = [vm['id'] for vm in vms]
        selections = get_selections(info)

        fields = []
        for s in selections:
            if s == 'info':
                fields.append('veil_info')
            elif s == 'name' and 'veil_info' not in fields:
                fields.append('veil_info')
            else:
                fields.append(s)

        if 'id' not in fields:
            fields.append('id')

        qu = f"SELECT {', '.join(fields)} FROM template_vm"
        data = await conn.fetch(qu)

        templates = [
            dict(zip(fields, t)) for t in data
        ]

        templates = [t for t in templates if t['id'] in vms]

        def make_template(t):
            if 'id' not in selections:
                t.pop('id', None)
            if 'veil_info' in t:
                t['info'] = t.pop('veil_info')

            if 'name' in selections:
                info = json.loads(t['info'])
                t['name'] = info['verbose_name']
            if 'info' not in selections:
                t.pop('info', None)
            return TemplateType(**t)

        return [
            make_template(t) for t in templates
        ]

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

