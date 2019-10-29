import graphene

import asyncio

from database import db

import graphene

#from .pool import PoolType, VmType, TemplateType
from utils import get_selections, make_resource_type
from database import get_list_of_values_from_db

from controller_resources.veil_client import ResourcesHttpClient

#from ..tasks import Token
#from ..tasks.vm import ListTemplates, ListVms

# from tasks.resources import (
#     DiscoverControllers, FetchNode, FetchCluster, DiscoverControllerIp, ListClusters,
#     ListDatapools, ListNodes, FetchResourcesUsage, CheckController
# )

from common.veil_errors import FieldError, SimpleError, FetchException, NotFound

#from vdi.resources_monitoring.resources_monitor_manager import resources_monitor_manager
from settings import DEFAULT_NAME

from controller.schema import ControllerType
from controller.models import Controller


class RequestType(graphene.ObjectType):
    url = graphene.String()
    time = graphene.String()


class DatacenterType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()


class ResourcesUsageType(graphene.ObjectType):
    cpu_used_percent = graphene.Float()
    mem_used_percent = graphene.Float()


class ClusterType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    nodes_count = graphene.Int()
    status = graphene.String()
    cpu_count = graphene.Int()
    memory_count = graphene.Int()
    tags = graphene.List(graphene.String)
    #vms = graphene.List(VmType, wild=graphene.Boolean())
    #templates = graphene.List(TemplateType)
    nodes = graphene.List(lambda: NodeType)
    datapools = graphene.List(lambda: DatapoolType)
    controller = graphene.Field(lambda: ControllerType)
    resources_usage = graphene.Field(ResourcesUsageType)

    async def resolve_nodes(self, info):
        return await self.controller.resolve_nodes(info, cluster_id=self.id)

    async def resolve_datapools(self, info):
        return await self.controller.resolve_datapools(info, cluster_id=self.id)

    # async def resolve_vms(self, info, wild=True):
    #     return await self.controller.resolve_vms(info, cluster_id=self.id, wild=wild)

    # async def resolve_templates(self, info):
    #     return await self.controller.resolve_templates(info, cluster_id=self.id)

    async def resolve_resources_usage(self, _info):
        resources_http_client = ResourcesHttpClient(self.controller.ip)
        return await resources_http_client.fetch_resources_usage('clusters', self.id)


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

    #vms = graphene.List(VmType, wild=graphene.Boolean())
    #templates = graphene.List(TemplateType)
    cluster = graphene.Field(lambda: ClusterType)
    datapools = graphene.List(lambda: DatapoolType)
    controller = graphene.Field(lambda: ControllerType)
    resources_usage = graphene.Field(ResourcesUsageType)

    veil_info = None  # dict

    async def get_veil_info(self):
        resources_http_client = ResourcesHttpClient(self.controller.ip)
        return await resources_http_client.fetch_node(self.id)

    async def resolve_verbose_name(self, info):
        if self.verbose_name:
            return self.verbose_name
        if self.veil_info is None:
            veil_info = await self.get_veil_info()
        if veil_info:
            return veil_info['verbose_name']
        else:
            return DEFAULT_NAME

    # async def resolve_vms(self, info, wild=True):
    #     return await self.controller.resolve_vms(info, node_id=self.id, wild=wild)

    # async def resolve_templates(self, info):
    #     return await self.controller.resolve_templates(info, node_id=self.id)

    async def resolve_datapools(self, info):
        return await self.controller.resolve_datapools(info, node_id=self.id)

    async def resolve_cluster(self, info):
        resources_http_client = ResourcesHttpClient(self.controller.ip)

        if self.veil_info is None:
            self.veil_info = await self.get_veil_info()
        cluster_id = self.veil_info['cluster']['id']

        resp = await resources_http_client.fetch_cluster(cluster_id)

        obj = make_resource_type(ClusterType, resp)
        obj.controller = self.controller
        return obj

    async def resolve_datacenter(self, info):
        if self.datacenter:
            return self.datacenter
        if self.veil_info is None:
            self.veil_info = await self.get_veil_info()
        return DatacenterType(id=self.veil_info['datacenter_id'],
                              verbose_name=self.veil_info['datacenter_name'])

    async def resolve_resources_usage(self, _info):
        resources_http_client = ResourcesHttpClient(self.controller.address)
        return await resources_http_client.fetch_resources_usage('nodes', self.id)

    async def resolve_management_ip(self, _info):
        if self.veil_info is None:
            self.veil_info = await self.get_veil_info()
        return self.veil_info['management_ip']


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
        resources_http_client = ResourcesHttpClient(self.controller.address)
        if not fields <= base_fields:
            for node in self.nodes:
                node_data = await resources_http_client.fetch_node(node['id'])
                obj = make_resource_type(NodeType, node_data)
                obj.controller = ControllerType(ip=self.controller_ip)
                nodes.append(obj)
        else:
            for node in self.nodes:
                obj = make_resource_type(NodeType, node)
                obj.controller = ControllerType(ip=self.controller_ip)
                nodes.append(obj)

        return nodes

    async def resolve_nodes_connected(self, info):
        return await self.resolve_nodes(info)

    controller_ip = None


class ResourcesQuery(graphene.ObjectType):

    node = graphene.Field(NodeType, id=graphene.String())
    nodes = graphene.List(NodeType, ordering=graphene.String(), reversed_order=graphene.Boolean())

    cluster = graphene.Field(ClusterType, id=graphene.String())
    clusters = graphene.List(ClusterType, ordering=graphene.String(), reversed_order=graphene.Boolean())

    datapool = graphene.Field(DatapoolType, id=graphene.String())
    datapools = graphene.List(DatapoolType, ordering=graphene.String(), reversed_order=graphene.Boolean())

    #template = graphene.Field(TemplateType, id=graphene.String())
    #vm = graphene.Field(VmType, id=graphene.String())

    requests = graphene.List(RequestType, time=graphene.Float())

    @staticmethod
    async def get_resource(_info, id, resource_type, function_to_get_resource_list, fields_map={}):
        # get all known controller ips
        controllers_ips = await get_list_of_values_from_db(Controller, Controller.address)

        # find out on which controller our resource is
        for controllers_ip in controllers_ips:
            # try to get list of resources
            try:
                resource_list = await function_to_get_resource_list(controller_ip=controllers_ip)
            except Exception:
                continue
            # find resource data by id
            try:
                data = next(data for data in resource_list if data['id'] == id)
                print('data', data)
                return make_resource_type(resource_type, data, fields_map)
            except StopIteration:
                pass
        # if we didnt find anything then return None
        return None

    async def resolve_node(self, _info, id):
        resources_http_client = ResourcesHttpClient()
        node_data = resources_http_client.get_node_data(id)
        fields = {
            k: v for k, v in node_data['resource_data'].items()
            if k in NodeType._meta.fields
        }
        return NodeType(controller=ControllerType(address=node_data['controller_address']), **fields)

    async def resolve_nodes(self, _info, ordering=None, reversed_order=None):
        resources_http_client = ResourcesHttpClient()
        controllers = await resources_http_client.discover_controllers(return_broken=False)

        # form list of nodes
        list_of_all_node_types = []

        for controller in controllers:
            nodes = await resources_http_client.fetch_node_list(controller['address'])
            node_type_list = []
            for node in nodes:
                obj = make_resource_type(NodeType, node)
                obj.controller = ControllerType(address=controller['address'])
                node_type_list.append(obj)

            list_of_all_node_types.extend(node_type_list)

        # sort list of nodes
        if ordering:
            if ordering == 'verbose_name':
                def sort_lam(node): return node.verbose_name if node.verbose_name else DEFAULT_NAME
            elif ordering == 'cpu_count':
                def sort_lam(node): return node.cpu_count if node.cpu_count else 0
            elif ordering == 'memory_count':
                def sort_lam(node): return node.memory_count if node.memory_count else 0
            elif ordering == 'datacenter_name':
                def sort_lam(node):
                    return node.cluster['datacenter_name'] if node.cluster['datacenter_name'] else DEFAULT_NAME
            elif ordering == 'status':
                def sort_lam(node): return node.status if node.status else DEFAULT_NAME
            elif ordering == 'controller':
                def sort_lam(node): return node.controller.ip if node.controller.ip else DEFAULT_NAME
            elif ordering == 'management_ip':
                def sort_lam(node): return node.management_ip if node.management_ip else DEFAULT_NAME
            else:
                raise SimpleError('Неверный параметр сортировки')
            reverse = reversed_order if reversed_order is not None else False
            list_of_all_node_types = sorted(list_of_all_node_types, key=sort_lam, reverse=reverse)

        return list_of_all_node_types

    async def resolve_cluster(self, _info, id):
        resources_http_client = ResourcesHttpClient()
        cluster_data = resources_http_client.fetch_cluster(id)
        fields = {
            k: v for k, v in cluster_data['resource_data'].items()
            if k in ClusterType._meta.fields
        }
        return ClusterType(controller=ControllerType(address=cluster_data['controller_address']), **fields)

    async def resolve_clusters(self, _info, ordering=None, reversed_order=None):
        resources_http_client = ResourcesHttpClient()
        controllers = await resources_http_client.discover_controllers(return_broken=False)
        print('test controllers', controllers)
        # form list of clusters
        list_of_all_cluster_types = []

        for controller in controllers:
            clusters = await resources_http_client.fetch_cluster_list(controller['address'])
            cluster_type_list = []
            for cluster in clusters:
                obj = make_resource_type(ClusterType, cluster)
                obj.controller = ControllerType(address=controller['ip'])
                cluster_type_list.append(obj)

            list_of_all_cluster_types.extend(cluster_type_list)

        # sort list of clusters
        if ordering:
            if ordering == 'verbose_name':
                def sort_lam(cluster): return cluster.verbose_name if cluster.verbose_name else DEFAULT_NAME
            elif ordering == 'cpu_count':
                def sort_lam(cluster): return cluster.cpu_count if cluster.cpu_count else 0
            elif ordering == 'memory_count':
                def sort_lam(cluster): return cluster.memory_count if cluster.memory_count else 0
            elif ordering == 'nodes_count':
                def sort_lam(cluster): return cluster.nodes_count if cluster.nodes_count else 0
            elif ordering == 'status':
                def sort_lam(cluster): return cluster.status if cluster.status else DEFAULT_NAME
            elif ordering == 'controller':
                def sort_lam(cluster): return cluster.controller.ip if cluster.controller.ip else DEFAULT_NAME
            else:
                raise SimpleError('Неверный параметр сортировки')
            reverse = reversed_order if reversed_order is not None else False
            list_of_all_cluster_types = sorted(list_of_all_cluster_types, key=sort_lam, reverse=reverse)

        return list_of_all_cluster_types

    async def resolve_datapool(self, _info, id):
        datapool = None
        #datapool = await ResourcesQuery.get_resource(_info, id, DatapoolType, ListDatapools)
        return datapool

    async def resolve_datapools(self, _info, take_broken=False,
                                ordering=None, reversed_order=None):
        controllers = None#await DiscoverControllers(return_broken=False)

        # form list of datapools
        list_of_all_datapool_types = []

        for controller in controllers:
            datapools = None#await ListDatapools(controller_ip=controller['ip'], take_broken=take_broken)
            datapool_type_list = []
            for datapool in datapools:
                obj = make_resource_type(DatapoolType, datapool)
                datapool_type_list.append(obj)

            list_of_all_datapool_types.extend(datapool_type_list)

        # sort list of datapools
        if ordering:
            if ordering == 'verbose_name':
                def sort_lam(datapool): return datapool.verbose_name if datapool.verbose_name else DEFAULT_NAME
                pass
            elif ordering == 'type':
                def sort_lam(datapool): return datapool.type if datapool.type else DEFAULT_NAME
            elif ordering == 'vdisk_count':
                def sort_lam(datapool): return datapool.vdisk_count if datapool.vdisk_count else 0
            elif ordering == 'iso_count':
                def sort_lam(datapool): return datapool.iso_count if datapool.iso_count else 0
            elif ordering == 'file_count':
                def sort_lam(datapool): return datapool.file_count if datapool.file_count else 0
            elif ordering == 'used_space':
                def sort_lam(datapool): return datapool.used_space if datapool.used_space else 0
            elif ordering == 'free_space':
                def sort_lam(datapool): return datapool.free_space if datapool.free_space else 0
            elif ordering == 'status':
                def sort_lam(datapool): return datapool.status if datapool.status else DEFAULT_NAME
            else:
                raise SimpleError('Неверный параметр сортировки')
            reverse = reversed_order if reversed_order is not None else False
            list_of_all_datapool_types = sorted(list_of_all_datapool_types, key=sort_lam, reverse=reverse)

        return list_of_all_datapool_types

    # async def resolve_template(self, _info, id):
    #     template = await ResourcesQuery.get_resource(_info, id, TemplateType, ListTemplates, {'verbose_name': 'name'})
    #     return template

    # async def resolve_vm(self, _info, id):
    #     vm = await ResourcesQuery.get_resource(_info, id, VmType, ListVms)
    #     return vm

    async def resolve_requests(self, _info):
        return [
            RequestType(url=None, time=None)
        ]


resources_schema = graphene.Schema(query=ResourcesQuery, auto_camelcase=False)
