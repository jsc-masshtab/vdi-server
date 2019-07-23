import socket

import graphene
from asyncpg.connection import Connection
from classy_async import wait

from .pool import PoolType, VmType, TemplateType
from .util import get_selections
from ..db import db
from ..tasks import resources, FetchException, Token
from ..tasks.vm import ListTemplates, ListVms
from ..tasks.resources import DiscoverControllers, FetchNode, FetchCluster, DiscoverController

from vdi.errors import FieldError, NotFound

class DatacenterType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()


class ClusterType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    nodes_count = graphene.Int()
    status = graphene.String()
    cpu_count = graphene.Int()
    memory_count = graphene.Int()
    tags = graphene.List(graphene.String)
    vms = graphene.List(VmType, wild=graphene.Boolean())
    templates = graphene.List(TemplateType)
    nodes = graphene.List(lambda: NodeType)
    datapools = graphene.List(lambda: DatapoolType)
    controller = graphene.Field(lambda: ControllerType)

    async def resolve_nodes(self, info):
        return await self.controller.resolve_nodes(info, cluster_id=self.id)

    async def resolve_templates(self, info):
        return await self.controller.resolve_templates(info, cluster_id=self.id)

    async def resolve_datapools(self, info):
        return await self.controller.resolve_datapools(info, cluster_id=self.id)

    async def resolve_vms(self, info, wild=False):
        return await self.controller.resolve_vms(info, cluster_id=self.id, wild=wild)

    info = None


#FIXME tests

class NodeType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    status = graphene.String()
    datacenter_id = graphene.String(deprecation_reason="Use `datacenter` field")
    datacenter_name = graphene.String(deprecation_reason="Use `datacenter` field")
    datacenter = graphene.Field(DatacenterType)
    cpu_count = graphene.String()
    memory_count = graphene.String()
    management_ip = graphene.String()

    vms = graphene.List(VmType, wild=graphene.Boolean())
    templates = graphene.List(TemplateType)
    cluster = graphene.Field(lambda: ClusterType)
    datapools = graphene.List(lambda: DatapoolType)
    controller = graphene.Field(lambda: ControllerType)



    async def resolve_nodes(self, info):
        return await self.controller.resolve_nodes(info, node_id=self.id)

    async def resolve_templates(self, info):
        return await self.controller.resolve_templates(info, node_id=self.id)

    async def resolve_datapools(self, info):
        return await self.controller.resolve_datapools(info, node_id=self.id)

    async def resolve_vms(self, info, wild=False):
        return await self.controller.resolve_vms(info, node_id=self.id, wild=wild)



    async def resolve_cluster(self, info):
        if self.info is None:
            self.info = await resources.FetchNode(controller_ip=self.controller.ip, node_id=self.id)
        cluster_id = self.info['cluster']['id']
        #TODO return immediately
        resp = await resources.FetchCluster(controller_ip=self.controller.ip, cluster_id=cluster_id)
        obj = self.controller._make_type(ClusterType, resp)
        obj.controller = self.controller
        return obj

    async def resolve_datacenter(self, info):
        if self.datacenter:
            return self.datacenter
        if self.info is None:
            self.info = await resources.FetchNode(controller_ip=self.controller.ip, node_id=self.id)
        return DatacenterType(id=self.info['datacenter_id'], verbose_name=self.info['datacenter_name'])

    info: dict = None


class DatapoolType(graphene.ObjectType):
    id = graphene.String()
    used_space = graphene.Int()
    free_space = graphene.Int()
    size = graphene.Int()
    status = graphene.String()
    type = graphene.String()
    vdisk_count = graphene.Int()
    tags = graphene.List(graphene.String)
    hints = graphene.List(graphene.String)
    file_count = graphene.Int()
    iso_count = graphene.Int()
    nodes = graphene.List(lambda: NodeType)
    nodes_connected = graphene.List(lambda: NodeType, deprecation_reason="Use `nodes`")
    verbose_name = graphene.String()

    async def resolve_nodes(self, info):
        base_fields = {'id', 'verbose_name'}
        fields = set(get_selections(info))
        nodes = []
        controller = ControllerType(ip=self.controller_ip)
        if not fields <= base_fields:
            tasks = [
                resources.FetchNode(controller_ip=self.controller_ip, node_id=node['id'])
                for node in self.nodes
            ]
            async for node in wait(*tasks):
                obj = controller._make_type(NodeType, node)
                obj.controller = ControllerType(ip=self.controller_ip)
                nodes.append(obj)
        else:
            for node in self.nodes:
                obj = controller._make_type(NodeType, node)
                obj.controller = ControllerType(ip=self.controller_ip)
                nodes.append(obj)

        return nodes

    async def resolve_nodes_connected(self, info):
        return await self.resolve_nodes(info)

    controller_ip = None
    info = None



class Resources:
    controllers = graphene.List(lambda: ControllerType)
    node = graphene.Field(NodeType, id=graphene.String())
    cluster = graphene.Field(ClusterType, id=graphene.String())

    async def resolve_controllers(self, info):
        objects = [
            ControllerType(**item)
            for item in await DiscoverControllers()
        ]
        return objects

    async def resolve_node(self, info, id):
        controller_ip = await DiscoverController(node_id=id)
        if not controller_ip:
            raise FieldError(id=['Узел с данным id не найден'])
        data = await FetchNode(controller_ip=controller_ip, node_id=id)
        fields = {
            k: v for k, v in data.items()
            if k in NodeType._meta.fields
        }
        return NodeType(controller=ControllerType(ip=controller_ip), **fields)

    async def resolve_cluster(self, info, id):
        controller_ip = await DiscoverController(cluster_id=id)
        if not controller_ip:
            raise FieldError(cluster_id=['Кластер с данным id не найден'])
        data = await FetchCluster(controller_ip=controller_ip, cluster_id=id)
        fields = {
            k: v for k, v in data.items()
            if k in ClusterType._meta.fields
        }
        return ClusterType(controller=ControllerType(ip=controller_ip), **fields)


class AddController(graphene.Mutation):
    class Arguments:
        ip = graphene.String(required=True)
        description = graphene.String(required=False)
        set_default = graphene.Boolean()

    ok = graphene.Boolean()

    @classmethod
    async def _add_controller(cls, ip, set_default=False, description=None):
        await Token(controller_ip=ip)
        try:
            resp = await resources.ListClusters(controller_ip=ip)
        except FetchException:
            return AddController(ok=False)

        async with db.connect() as conn:
            query = f'''
            INSERT INTO controller (ip, description) VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            ''', ip, description
            await conn.execute(*query)

        if set_default:
            async with db.connect() as conn:
                [(exists,)] = await conn.fetch("SELECT COUNT(*) FROM default_controller")
                if not exists:
                    query = "INSERT INTO default_controller (ip) VALUES ($1)", ip
                    await conn.fetch(*query)
                else:
                    query = "UPDATE default_controller SET ip = $1", ip
                    await conn.fetch(*query)

    async def mutate(self, info, ip, set_default=False, description=None):
        await AddController._add_controller(ip=ip, set_default=set_default, description=description)
        return AddController(ok=True)


class RemoveController(graphene.Mutation):
    class Arguments:
        controller_ip = graphene.String()

    ok = graphene.Boolean()

    @classmethod
    async def _remove_pools(cls, *, controller_ip):
        async with db.connect() as c:
            qu = "SELECT id FROM pool WHERE controller_ip = $1 AND deleted IS NOT TRUE", controller_ip
            pools = await c.fetch(*qu)

        from vdi.graphql.pool import RemovePool
        tasks = [
            RemovePool.do_remove(pool['id'], controller_ip=controller_ip)
            for pool in pools
        ]
        async for _ in wait(*tasks):
            pass


    async def mutate(self, info, controller_ip):
        async with db.connect() as conn:
            await RemoveController._remove_pools(controller_ip=controller_ip)
            query = "DELETE FROM default_controller WHERE ip = $1", controller_ip
            await conn.fetch(*query)
            query = f"DELETE FROM controller WHERE ip=$1", controller_ip
            await conn.execute(*query)

        return RemoveController(ok=True)


class ControllerType(graphene.ObjectType):
    ip = graphene.String()
    description = graphene.String()
    default = graphene.Boolean()


    templates = graphene.List(TemplateType,
                              cluster_id=graphene.String(), node_id=graphene.String())
    vms = graphene.List(VmType,
                        cluster_id=graphene.String(), node_id=graphene.String(),
                        wild=graphene.Boolean())

    datapools = graphene.List(DatapoolType,
                              node_id=graphene.String(),
                              cluster_id=graphene.String())
    clusters = graphene.List(ClusterType)
    cluster = graphene.Field(ClusterType, id=graphene.String())
    nodes = graphene.List(NodeType, cluster_id=graphene.String())
    node = graphene.Field(NodeType, id=graphene.String())


    async def resolve_templates(self, info, cluster_id=None, node_id=None):
        if node_id is not None:
            nodes = {node_id}
        elif cluster_id is not None:
            nodes = await resources.ListNodes(controller_ip=self.ip, cluster_id=cluster_id)
            nodes = {node['id'] for node in nodes}
        else:
            nodes = None
        vms = await ListTemplates(controller_ip=self.ip)
        if nodes is not None:
            vms = [
                vm for vm in vms
                if vm['node']['id'] in nodes
            ]
        objects = []
        for vm in vms:
            node = NodeType(id=vm['node']['id'], verbose_name=vm['node']['verbose_name'])
            node.controller = self
            obj = TemplateType(name=vm['verbose_name'], info=vm, id=vm['id'], node=node)
            obj.controller_ip = self.ip
            objects.append(obj)
        return objects

    async def resolve_vms(self, info, cluster_id=None, node_id=None, wild=False):
        if node_id is not None:
            nodes = {node_id}
        elif cluster_id is not None:
            nodes = await resources.ListNodes(controller_ip=self.ip, cluster_id=cluster_id)
            nodes = {node['id'] for node in nodes}
        else:
            nodes = None
        vms = await ListVms(controller_ip=self.ip)
        if nodes is not None:
            vms = [
                vm for vm in vms
                if vm['node']['id'] in nodes
            ]
        vm_ids = {vm['id']: None for vm in vms}
        if not wild:
            async with db.connect() as conn:
                qu = "select id, pool_id from vm where id = any($1::text[])", list(vm_ids)
                data = await conn.fetch(*qu)
                vm_ids = {item['id']: item['pool_id'] for item in data}

        objects = []
        for vm in vms:
            if vm['id'] not in vm_ids:
                continue
            node = NodeType(id=vm['node']['id'], verbose_name=vm['node']['verbose_name'])
            node.controller = self
            pool_id = vm_ids[vm['id']]
            if pool_id:
                pool_kwargs = {'pool': PoolType(id=pool_id, controller=self)}
            else:
                pool_kwargs = {}
            obj = VmType(name=vm['verbose_name'], id=vm['id'], node=node, **pool_kwargs)
            obj.selections = get_selections(info)
            obj.info = vm
            if not pool_id:
                obj.controller_ip = self.ip

            objects.append(obj)
        return objects

    def _make_type(self, type, data, fields_map=None):
        dic = {}
        for k, v in data.items():
            if fields_map:
                k = fields_map.get(k, k)
            if k in type._meta.fields:
                dic[k] = v
        obj = type(**dic)
        obj.info = data
        return obj

    async def resolve_datapools(self, info, node_id=None, cluster_id=None):
        controller_ip = self.ip
        if node_id is not None:
            return self._get_datapools(info, node_id=node_id)
        if cluster_id is not None:
            cluster_ids = [cluster_id]
        else:
            clusters = await resources.ListClusters(controller_ip=controller_ip)
            cluster_ids = [c['id'] for c in clusters]
        datapools = {}

        for cluster_id in cluster_ids:
            nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
            for node in nodes:
                objects = await self._get_datapools(info, node_id=node['id'])
                datapools.update(
                    (obj.id, obj) for obj in objects
                )
        datapools = list(datapools.values())
        return datapools

    # TODO fields/info rework

    async def _get_datapools(self, info, node_id):
        resp = await resources.ListDatapools(controller_ip=self.ip, node_id=node_id)
        fields = get_selections(info)

        li = []
        for item in resp:
            obj = self._make_type(DatapoolType, item, {'nodes_connected': 'nodes'})
            obj.controller_ip = self.ip
            li.append(obj)

        return li

    async def resolve_clusters(self, info):
        controller_ip = self.ip
        resp = await resources.ListClusters(controller_ip)
        li = []
        for item in resp:
            obj = self._make_type(ClusterType, item)
            obj.controller = self
            obj.nodes = []
            li.append(obj)
        return li

    async def resolve_cluster(self, info, *, id):
        controller_ip = self.ip
        try:
            resp = await resources.FetchCluster(controller_ip=controller_ip, cluster_id=id)
        except NotFound:
            raise FieldError(id=['Кластер не найден'])
        obj = self._make_type(ClusterType, resp)
        obj.controller = self
        return obj

    async def _get_nodes(self, info, *, cluster_id):
        nodes = await resources.ListNodes(controller_ip=self.ip, cluster_id=cluster_id)
        li = []
        for node in nodes:
            obj = self._make_type(NodeType, node)
            obj.controller = self
            li.append(obj)
        return li

    async def resolve_nodes(self, info, cluster_id=None):
        controller_ip = self.ip
        if cluster_id is not None:
            return await self._get_nodes(info, cluster_id=cluster_id)
        result = {}
        clusters = await resources.ListClusters(controller_ip=controller_ip)
        for cluster in clusters:
            nodes = await self._get_nodes(info, cluster_id=cluster['id'])
            result.update(
                (obj.id, obj) for obj in nodes
            )
        return list(result.values())

    async def resolve_node(self, info, id):
        controller_ip = self.ip
        node = await resources.FetchNode(controller_ip=controller_ip, node_id=id)
        obj = self._make_type(NodeType, node)
        obj.controller = self
        return obj