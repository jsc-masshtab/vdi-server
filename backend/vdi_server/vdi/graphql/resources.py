


import graphene
from graphql import GraphQLError

from asyncpg.connection import Connection
from classy_async import wait

from ..db import db
from ..tasks import resources, FetchException, vm

from .util import get_selections
from vdi.context_utils import enter_context

from .pool import PoolSettings, TemplateType, VmType


class ControllerType(graphene.ObjectType):
    ip = graphene.String()
    description = graphene.String()
    default = graphene.Boolean()


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
    nodes = graphene.List(lambda: NodeType)
    templates = graphene.List(lambda: TemplateType)
    vms = graphene.List(lambda: VmType)
    datapools = graphene.List(lambda: DatapoolType)

    async def resolve_nodes(self, info):
        li = await Resources.resolve_nodes(None, info, controller_ip=self.controller_ip, cluster_id=self.id)
        for obj in li:
            obj.cluster = self
        return li

    async def resolve_templates(self, info):
        from vdi.graphql.vm import TemplateMixin
        return await TemplateMixin.resolve_templates(None, info, controller_ip=self.controller_ip, cluster_id=self.id)

    async def resolve_datapools(self, info):
        return await Resources.resolve_datapools(None, info, controller_ip=self.controller_ip, cluster_id=self.id)

    async def resolve_vms(self, info):
        from vdi.graphql.vm import TemplateMixin
        return await TemplateMixin.resolve_vms(None, info, controller_ip=self.controller_ip, cluster_id=self.id)

    controller_ip = None
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

    cluster = graphene.Field(lambda: ClusterType)
    datapools = graphene.List(lambda: DatapoolType)
    vms = graphene.List(lambda: VmType)
    templates = graphene.List(lambda: TemplateType)

    async def resolve_templates(self, info):
        from vdi.graphql.vm import TemplateMixin
        li = await TemplateMixin.resolve_templates(None, info, controller_ip=self.controller_ip, node_id=self.id)
        for obj in li:
            obj.node = self
        return li

    async def resolve_vms(self, info):
        from vdi.graphql.vm import TemplateMixin
        li = await TemplateMixin.resolve_vms(None, info, controller_ip=self.controller_ip, node_id=self.id)
        for obj in li:
            obj.node = self
        return li

    async def resolve_datapools(self, info):
        return await Resources.resolve_datapools(None, info, controller_ip=self.controller_ip, node_id=self.id)

    async def resolve_cluster(self, info):
        if self.info is None:
            self.info = await resources.FetchNode(controller_ip=self.controller_ip, node_id=self.id)
        cluster_id = self.info['cluster']['id']
        resp = await resources.FetchCluster(controller_ip=self.controller_ip, cluster_id=cluster_id)
        obj = Resources._make_type(ClusterType, resp)
        obj.controller_ip = self.controller_ip
        return obj

    def resolve_datacenter(self, info):
        if self.datacenter:
            return self.datacenter
        return DatacenterType(id=self.info['datacenter_id'], verbose_name=self.info['datacenter_name'])


    controller_ip = None
    info = None


#TODO remove template flag from the db
#TODO controller_ip as var

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
        if not fields <= base_fields:
            tasks = [
                resources.FetchNode(controller_ip=self.controller_ip, node_id=node['id'])
                for node in self.nodes
            ]
            async for node in wait(*tasks):
                obj = Resources._make_type(NodeType, node)
                obj.controller_ip = self.controller_ip
                nodes.append(obj)
        else:
            for node in self.nodes:
                obj = Resources._make_type(NodeType, node)
                obj.controller_ip = self.controller_ip
                nodes.append(obj)

        return nodes

    async def resolve_nodes_connected(self, info):
        return await self.resolve_nodes(info)

    controller_ip = None
    info = None



@enter_context(lambda: db.connect())
async def get_controller_ip(conn: Connection):
    res = await conn.fetch("SELECT ip FROM default_controller LIMIT 1")
    if not res:
        return None
    [(ip,)] = res
    return ip



class Resources:
    datapools = graphene.List(DatapoolType,
                              node_id=graphene.String(),
                              controller_ip=graphene.String(),
                              cluster_id=graphene.String()
                              )
    clusters = graphene.List(ClusterType,
                             controller_ip=graphene.String())
    cluster = graphene.Field(ClusterType, id=graphene.String(), controller_ip=graphene.String())
    nodes = graphene.List(NodeType,
                          controller_ip=graphene.String(),
                          cluster_id=graphene.String())
    node = graphene.Field(NodeType, id=graphene.String(), controller_ip=graphene.String())
    controllers = graphene.List(ControllerType)

    @classmethod
    def _make_type(cls, type, data, fields_map=None):
        dic = {}
        for k, v in data.items():
            if fields_map:
                k = fields_map.get(k, k)
            if k in type._meta.fields:
                dic[k] = v
        obj = type(**dic)
        obj.info = data
        return obj

    async def resolve_datapools(self, info, controller_ip=None, node_id=None, cluster_id=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        if node_id is not None:
            return Resources._get_datapools(info, controller_ip=controller_ip, node_id=node_id)
        if cluster_id is not None:
            cluster_ids = [cluster_id]
        else:
            clusters = await resources.ListClusters(controller_ip=controller_ip)
            cluster_ids = [c['id'] for c in clusters]
        datapools = {}

        for cluster_id in cluster_ids:
            nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
            for node in nodes:
                objects = await Resources._get_datapools(info, controller_ip=controller_ip, node_id=node['id'])
                datapools.update(
                    (obj.id, obj) for obj in objects
                )
        datapools = list(datapools.values())
        return datapools

    #TODO fields/info rework

    @classmethod
    async def _get_datapools(cls, info, controller_ip, node_id):
        resp = await resources.ListDatapools(controller_ip=controller_ip, node_id=node_id)
        fields = get_selections(info)

        li = []
        for item in resp:
            obj = Resources._make_type(DatapoolType, item, {'nodes_connected': 'nodes'})
            obj.controller_ip = controller_ip
            li.append(obj)

        return li

    async def resolve_clusters(self, info, controller_ip=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        resp = await resources.ListClusters(controller_ip)
        li = []
        for item in resp:
            obj = Resources._make_type(ClusterType, item)
            obj.controller_ip = controller_ip
            obj.nodes = []
            li.append(obj)
        return li

    async def resolve_cluster(self, info, id=None, controller_ip=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        if id is None:
            from vdi.tasks.admin import discover_resources
            discovered = await discover_resources()
            [id] = discovered['clusters']
        resp = await resources.FetchCluster(controller_ip=controller_ip, cluster_id=id)
        obj = Resources._make_type(ClusterType, resp)
        obj.controller_ip = controller_ip
        return obj

    @classmethod
    async def _get_nodes(cls, info, controller_ip, cluster_id):
        nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
        li = []
        for node in nodes:
            obj = Resources._make_type(NodeType, node)
            obj.controller_ip = controller_ip
            li.append(obj)
        return li

    async def resolve_nodes(self, info, controller_ip=None, cluster_id=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        if cluster_id is not None:
            return await Resources._get_nodes(info, controller_ip, cluster_id)
        result = {}
        clusters = await resources.ListClusters(controller_ip=controller_ip)
        for cluster in clusters:
            nodes = await Resources._get_nodes(info, controller_ip, cluster['id'])
            result.update(
                (obj.id, obj) for obj in nodes
            )
        return list(result.values())

    @enter_context(lambda: db.connect())
    async def resolve_controllers(conn: Connection, self, info):
        default = await conn.fetch("SELECT ip FROM default_controller")
        if default:
            [(default,)] = default
        else:
            default = None
        query = "SELECT ip, description from controller"
        items = await conn.fetch(query)
        return [
            ControllerType(**dict(d.items()))
            for d in items
        ]

    async def resolve_node(self, info, id, controller_ip=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        node = await resources.FetchNode(controller_ip=controller_ip, node_id=id)
        obj = Resources._make_type(NodeType, node)
        obj.controller_ip = controller_ip
        return obj



class AddController(graphene.Mutation):
    class Arguments:
        ip = graphene.String(required=True)
        description = graphene.String(required=False)
        set_default = graphene.Boolean()

    ok = graphene.Boolean()

    @classmethod
    @enter_context(lambda: db.connect())
    async def _add_controller(conn: Connection, cls, ip, set_default=False, description=None):
        try:
            resp = await resources.ListClusters(controller_ip=ip)
        except FetchException:
            return AddController(ok=False)

        query = f'''
        INSERT INTO controller (ip, description) VALUES ($1, $2)
        ON CONFLICT DO NOTHING
        ''', ip, description

        await conn.execute(*query)

        if set_default:
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
    async def remove_pools(cls, *, controller_ip, conn: Connection):
        async with db.connect() as c:
            qu = "SELECT id FROM pool WHERE controller_ip = $1", controller_ip
            pools = await c.fetch(*qu)

        from vdi.graphql.pool import RemovePool
        tasks = [
            RemovePool.do_remove(pool['id'])
            for pool in pools
        ]
        async for _ in wait(*tasks):
            pass


    @enter_context(lambda: db.transaction())
    async def mutate(conn: Connection, self, info, controller_ip=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        await RemoveController.remove_pools(controller_ip=controller_ip, conn=conn)
        query = "DELETE FROM default_controller WHERE ip = $1", controller_ip
        await conn.fetch(*query)
        query = f"DELETE FROM controller WHERE ip=$1", controller_ip
        await conn.execute(*query)

        return RemoveController(ok=True)


