


import graphene
from graphql import GraphQLError

from asyncpg.connection import Connection
from classy_async import wait

from ..db import db
from ..tasks import resources, FetchException, vm

from .util import get_selections
from vdi.context_utils import enter_context

from .pool import PoolSettings


class ControllerType(graphene.ObjectType):
    ip = graphene.String()
    description = graphene.String()


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

#FIXME tests

class NodeType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    status = graphene.String()
    #FIXME
    datacenter_id = graphene.String(deprecation_reason="Use `datacenter` field")
    datacenter_name = graphene.String(deprecation_reason="Use `datacenter` field")
    datacenter = graphene.Field(DatacenterType)
    cpu_count = graphene.String()
    memory_count = graphene.String()
    management_ip = graphene.String()
    cluster = graphene.Field(lambda: ClusterType)


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
    nodes_connected = graphene.List(lambda: NodeType)
    verbose_name = graphene.String()




@enter_context(lambda: db.connect())
async def get_controller_ip(conn: Connection):
    res = await conn.fetch("SELECT ip FROM default_controller LIMIT 1")
    [(ip,)] = res
    return ip


class Resources:
    datapools = graphene.List(DatapoolType,
                              node_id=graphene.String(),
                              controller_ip=graphene.String(),
                              )
    clusters = graphene.List(ClusterType,
                             controller_ip=graphene.String())
    nodes = graphene.List(NodeType,
                          controller_ip=graphene.String(),
                          cluster_id=graphene.String())
    node = graphene.Field(NodeType, id=graphene.String(), controller_ip=graphene.String())
    controllers = graphene.List(ControllerType)
    poolwizard = graphene.Field(PoolSettings)

    @classmethod
    def _make_type(cls, type, item, selections):
        dic = {
            k: v for k, v in item.items()
            if k in type._meta.fields
        }
        return type(**dic)

    async def resolve_datapools(self, info, controller_ip=None, node_id=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        if node_id is not None:
            return Resources._get_datapools(info, controller_ip=controller_ip, node_id=node_id)
        datapools = {}
        clusters = await resources.ListClusters(controller_ip=controller_ip)
        for cluster in clusters:
            nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster['id'])
            for node in nodes:
                objects = await Resources._get_datapools(info, controller_ip=controller_ip, node_id=node['id'])
                datapools.update(
                    (obj.id, obj) for obj in objects
                )
        datapools = list(datapools.values())
        return datapools

    @classmethod
    async def _get_datapools(cls, info, controller_ip, node_id):
        resp = await resources.ListDatapools(controller_ip=controller_ip, node_id=node_id)
        fields = get_selections(info)

        li = []
        for item in resp:
            obj = Resources._make_type(DatapoolType, item, fields)
            if 'nodes_connected' in fields:
                base_fields = {'id', 'verbose_name'}
                node_fields = set(get_selections(info, 'nodes_connected'))
                if not node_fields <= base_fields:
                    tasks = [
                        resources.FetchNode(controller_ip=controller_ip, node_id=node['id'])
                        for node in obj.nodes_connected
                    ]
                    nodes = []
                    async for n in wait(*tasks):
                        n = Resources._make_node(n, node_fields)
                        nodes.append(n)
                else:
                    nodes = [
                        Resources._make_node(node, node_fields)
                        for node in obj.nodes_connected
                    ]
                obj.nodes_connected = nodes
            li.append(obj)

        return li

    async def resolve_clusters(self, info, controller_ip=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        resp = await resources.ListClusters(controller_ip)
        fields = get_selections(info)
        return [
            Resources._make_type(ClusterType, item, fields)
            for item in resp
        ]

    @classmethod
    def _make_node(cls, item, fields):
        obj = Resources._make_type(NodeType, item, fields)
        if 'datacenter' in fields:
            obj.datacenter = DatacenterType(id=item['datacenter_id'], verbose_name=item['datacenter_name'])
        if 'cluster' in fields:
            obj.cluster = ClusterType(**obj.cluster)
        return obj

    @classmethod
    async def _get_nodes(cls, info, controller_ip, cluster_id):
        nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
        fields = get_selections(info)

        li = []
        for node in nodes:
            obj = Resources._make_node(node, fields)
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
        query = "SELECT ip, description from controller"
        items = await conn.fetch(query)
        return [
            ControllerType(**dict(d.items()))
            for d in items
        ]

    @enter_context(lambda: db.connect())
    async def resolve_poolwizard(conn: Connection, self, info):
        import string, random
        uid = ''.join(
            random.choice(string.ascii_letters) for _ in range(3)
        )
        name = f"wizard-{uid}"
        controller_ip = '192.168.20.120'
        resp = await resources.ListClusters(controller_ip=controller_ip)
        [cluster] = resp
        resp = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster['id'])
        [node] = resp
        [datapool] = await resources.ListDatapools(controller_ip=controller_ip, node_id=node['id'])

        params = {
            'initial_size': 1,
            'reserve_size': 1,
            'controller_ip': controller_ip,
            'cluster_id': cluster['id'],
            'datapool_id': datapool['id'],
            'node_id': node['id'],
        }
        return PoolSettings(**params)

    async def resolve_node(self, info, id, controller_ip=None):
        if controller_ip is None:
            controller_ip = await get_controller_ip()
        fields = get_selections(info)
        node = await resources.FetchNode(controller_ip=controller_ip, node_id=id)
        return Resources._make_node(node, fields)


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

