


import graphene
from graphql import GraphQLError

from asyncpg.connection import Connection

from ..db import db
from ..tasks import resources, FetchException

from .util import get_selections
from vdi.context_utils import enter_context


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



class NodeType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    status = graphene.String()
    datacenter_id = graphene.String()
    datacenter_name = graphene.String()
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



class Resources:
    datapools = graphene.List(DatapoolType,
                              node_id=graphene.String(required=False),
                              controller_ip=graphene.String(),
                              # controller_id=graphene.String(required=False),
                              )

    clusters = graphene.List(ClusterType,
                             controller_ip=graphene.String())

    nodes = graphene.List(NodeType,
                          controller_ip=graphene.String(),
                          cluster_id=graphene.String(required=False))

    controllers = graphene.List(ControllerType)

    @classmethod
    def _make_type(cls, type, item, selections):
        dic = {
            k: v for k, v in item.items()
            if k in type._meta.fields
        }
        return type(**dic)

    @classmethod
    async def _get_node_id(cls, controller_ip):
        #TODO warning
        resp = await resources.ListClusters(controller_ip=controller_ip)
        [cluster] = resp['results']
        resp = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster['id'])
        [node] = resp['results']
        return node['id']

    async def resolve_datapools(self, info, controller_ip, node_id=None): #, controller_id=None):
        if node_id is None:
            node_id = await Resources._get_node_id(controller_ip)
        resp = await resources.ListDatapools(controller_ip=controller_ip, node_id=node_id)
        fields = get_selections(info)
        return {
            Resources._make_type(DatapoolType, item, fields)
            for item in resp
        }


    async def resolve_clusters(self, info, controller_ip):
        resp = await resources.ListClusters(controller_ip)
        fields = get_selections(info)
        return [
            Resources._make_type(ClusterType, item, fields)
            for item in resp['results']
        ]

    async def resolve_nodes(self, info, controller_ip, cluster_id=None):
        if cluster_id is None:
            resp = await resources.ListClusters(controller_ip=controller_ip)
            [cluster] = resp['results']
            cluster_id = cluster['id']
        resp = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
        fields = get_selections(info)
        return [
            Resources._make_type(NodeType, item, fields)
            for item in resp['results']
        ]

    @enter_context(lambda: db.connect())
    async def resolve_controllers(conn: Connection, self, info):
        query = "SELECT ip, description from controller"
        items = await conn.fetch(query)
        return [
            ControllerType(**dict(d.items()))
            for d in items
        ]



class AddController(graphene.Mutation):
    class Arguments:
        ip = graphene.String(required=True)
        description = graphene.String(required=False)

    ok = graphene.Boolean()

    @enter_context(lambda: db.connect())
    async def mutate(conn: Connection, self, info, ip, description=None):
        try:
            resp = await resources.ListClusters(controller_ip=ip)
        except FetchException:
            return AddController(ok=False)

        query = '''
        INSERT INTO controller (ip, description) VALUES ($1, $2)
        ON CONFLICT DO NOTHING
        ''', ip, description

        await conn.fetch(*query)

        return AddController(ok=True)

