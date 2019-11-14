import graphene

from vm.veil_client import VmHttpClient
from vm.schema import VmType, TemplateType, VmQuery

from common.utils import get_selections, make_graphene_type, extract_ordering_data
from common.veil_errors import FieldError, SimpleError, FetchException, NotFound

from controller_resources.veil_client import ResourcesHttpClient
from controller.schema import ControllerType
from controller.models import Controller

from settings import DEFAULT_NAME


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

    vms = graphene.List(VmType, wild=graphene.Boolean())
    templates = graphene.List(TemplateType)

    nodes = graphene.List(lambda: NodeType)
    datapools = graphene.List(lambda: DatapoolType)
    controller = graphene.Field(lambda: ControllerType)
    resources_usage = graphene.Field(ResourcesUsageType)

    async def resolve_nodes(self, _info):
        resources_http_client = await ResourcesHttpClient.create(self.controller.address)
        nodes = await resources_http_client.fetch_node_list(cluster_id=id)
        node_type_list = await ResourcesQuery.resource_veil_to_graphene_type_list(
            NodeType, nodes, self.controller.address)
        return node_type_list

    async def resolve_datapools(self, _info):
        resources_http_client = await ResourcesHttpClient.create(self.controller.address)

        datapools = []
        node_list = await resources_http_client.fetch_node_list(cluster_id=id)
        for node in node_list:
            datapool_list = await resources_http_client.fetch_datapool_list(node['id'])
            datapools.extend(datapool_list)

        datapool_type_list = await ResourcesQuery.resource_veil_to_graphene_type_list(
            DatapoolType, datapools, self.controller.address)
        return datapool_type_list

    async def resolve_vms(self, _info):
        vm_http_client = await VmHttpClient.create(self.controller.address, '')
        vms_list = await vm_http_client.fetch_vms_list(cluster_id=self.id)
        vm_type_list = VmQuery.veil_vm_data_to_graphene_type(vms_list, self.controller.address)
        return vm_type_list

    async def resolve_templates(self, _info):
        vm_http_client = await VmHttpClient.create(self.controller.address, '')
        template_list = await vm_http_client.fetch_templates_list(cluster_id=self.id)

        template_type_list = []
        for template in template_list:
            template_type = TemplateType(verbose_name=template['verbose_name'], id=template['id'])
            template_type.veil_info = template
            template_type_list.append(template_type)

        return template_type_list

    async def resolve_resources_usage(self, _info):
        resources_http_client = await ResourcesHttpClient.create(self.controller.address)
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

    vms = graphene.List(VmType, wild=graphene.Boolean())
    templates = graphene.List(TemplateType)
    cluster = graphene.Field(ClusterType)
    datapools = graphene.List(lambda: DatapoolType)
    controller = graphene.Field(ControllerType)
    resources_usage = graphene.Field(ResourcesUsageType)

    veil_info = None  # dict

    async def get_veil_info(self):
        resources_http_client = await ResourcesHttpClient.create(self.controller.address)
        return await resources_http_client.fetch_node(self.id)

    async def resolve_verbose_name(self, _info):
        if self.verbose_name:
            return self.verbose_name
        if self.veil_info is None:
            self.veil_info = await self.get_veil_info()
        if self.veil_info:
            return self.veil_info['verbose_name']
        else:
            return DEFAULT_NAME

    async def resolve_vms(self, _info):
        vm_http_client = await VmHttpClient.create(self.controller.address, '')
        vm_veil_data_list = await vm_http_client.fetch_vms_list(node_id=self.id)
        return VmQuery.veil_vm_data_to_graphene_type_list(vm_veil_data_list, self.controller.address)

    async def resolve_templates(self, _info):
        vm_http_client = await VmHttpClient.create(self.controller.address, '')
        template_veil_data_list = await vm_http_client.fetch_templates_list(node_id=self.id)
        return VmQuery.veil_template_data_to_graphene_type_list(template_veil_data_list, self.controller.address)

    async def resolve_datapools(self, _info):
        resources_http_client = await ResourcesHttpClient.create(self.controller.address)
        datapools = await resources_http_client.fetch_datapool_list(node_id=self.id)

        datapool_type_list = await ResourcesQuery.resource_veil_to_graphene_type_list(
            DatapoolType, datapools, self.controller.address)
        return datapool_type_list

    async def resolve_cluster(self, _info):
        resources_http_client = await ResourcesHttpClient.create(self.controller.address)

        if self.veil_info is None:
            self.veil_info = await self.get_veil_info()
        cluster_id = self.veil_info['cluster']['id']

        veil_cluster_data = await resources_http_client.fetch_cluster(cluster_id)
        cluster_type = make_graphene_type(ClusterType, veil_cluster_data)
        cluster_type.controller = self.controller
        return cluster_type

    async def resolve_datacenter(self, _info):
        await self.get_datacenter_data()
        return self.datacenter

    async def get_datacenter_data(self):
        if not self.datacenter:
            if self.veil_info is None:
                self.veil_info = await self.get_veil_info()
            self.datacenter = DatacenterType(id=self.veil_info['datacenter_id'],
                                  verbose_name=self.veil_info['datacenter_name'])

    async def resolve_resources_usage(self, _info):
        resources_http_client = await ResourcesHttpClient.create(self.controller.address)
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

    async def resolve_nodes(self, _info):
        resources_http_client = await ResourcesHttpClient.create(self.controller.address)
        nodes = await resources_http_client.fetch_node_list()
        node_type_list = await ResourcesQuery.resource_veil_to_graphene_type_list(
            NodeType, nodes, self.controller.address)
        return node_type_list

    async def resolve_nodes_connected(self, info):
        return await self.resolve_nodes(info)

    controller_ip = None


class ResourcesQuery(graphene.ObjectType):

    node = graphene.Field(NodeType, id=graphene.String(), controller_address=graphene.String())
    nodes = graphene.List(NodeType, ordering=graphene.String())

    cluster = graphene.Field(ClusterType, id=graphene.String(), controller_address=graphene.String())
    clusters = graphene.List(ClusterType, ordering=graphene.String())

    datapool = graphene.Field(DatapoolType, id=graphene.String(), controller_address=graphene.String())
    datapools = graphene.List(DatapoolType, ordering=graphene.String())

    requests = graphene.List(RequestType, time=graphene.Float())

    @staticmethod
    async def resource_veil_to_graphene_type_list(graphene_type, veil_resources_list, controller_address):
        """Convert veil resource data list to graphene resource data list"""
        graphene_type_type_list = []
        for resource_data in veil_resources_list:
            obj = make_graphene_type(graphene_type, resource_data)
            obj.controller = ControllerType(address=controller_address)
            graphene_type_type_list.append(obj)
        return graphene_type_type_list

    async def resolve_node(self, _info, id, controller_address):
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        node_data = await resources_http_client.fetch_node(id)
        node_type = make_graphene_type(NodeType, node_data)
        node_type.controller = ControllerType(address=controller_address)
        return node_type

    async def resolve_nodes(self, _info, ordering=None):
        controllers_addresses = await Controller.get_controllers_addresses()

        # form list of nodes
        list_of_all_node_types = []

        for controllers_address in controllers_addresses:
            resources_http_client = await ResourcesHttpClient.create(controllers_address)
            nodes = await resources_http_client.fetch_node_list()

            node_type_list = await ResourcesQuery.resource_veil_to_graphene_type_list(
                NodeType, nodes, controllers_address)
            list_of_all_node_types.extend(node_type_list)

        # sort list of nodes
        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)

            if ordering == 'verbose_name':
                def sort_lam(node): return node.verbose_name if node.verbose_name else DEFAULT_NAME
            elif ordering == 'cpu_count':
                def sort_lam(node): return node.cpu_count if node.cpu_count else 0
            elif ordering == 'memory_count':
                def sort_lam(node): return node.memory_count if node.memory_count else 0
            elif ordering == 'datacenter_name':
                for node_type in list_of_all_node_types:
                    await node_type.get_datacenter_data()

                def sort_lam(node):
                    return node.datacenter.verbose_name if node.datacenter.verbose_name else DEFAULT_NAME
            elif ordering == 'status':
                def sort_lam(node): return node.status if node.status else DEFAULT_NAME
            elif ordering == 'controller':
                def sort_lam(node): return node.controller.address if node.controller.address else DEFAULT_NAME
            elif ordering == 'management_ip':
                def sort_lam(node): return node.management_ip if node.management_ip else DEFAULT_NAME
            else:
                raise SimpleError('Неверный параметр сортировки')

            list_of_all_node_types = sorted(list_of_all_node_types, key=sort_lam, reverse=reverse)

        return list_of_all_node_types

    async def resolve_cluster(self, _info, id, controller_address):
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        cluster_data = await resources_http_client.fetch_cluster(id)
        cluster_type = make_graphene_type(ClusterType, cluster_data)
        cluster_type.controller = ControllerType(address=controller_address)
        return cluster_type

    async def resolve_clusters(self, _info, ordering=None):
        controllers_addresses = await Controller.get_controllers_addresses()
        print('test controllers', controllers_addresses)
        # form list of clusters
        list_of_all_cluster_types = []

        for controllers_address in controllers_addresses:
            resources_http_client = await ResourcesHttpClient.create(controllers_address)
            clusters = await resources_http_client.fetch_cluster_list()

            cluster_type_list = await ResourcesQuery.resource_veil_to_graphene_type_list(
                ClusterType, clusters, controllers_address)
            list_of_all_cluster_types.extend(cluster_type_list)

        # sort list of clusters
        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)

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
                def sort_lam(cluster): return cluster.controller.address if cluster.controller.address else DEFAULT_NAME
            else:
                raise SimpleError('Неверный параметр сортировки')
            list_of_all_cluster_types = sorted(list_of_all_cluster_types, key=sort_lam, reverse=reverse)

        return list_of_all_cluster_types

    async def resolve_datapool(self, _info, id, controller_address):
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        datapool_data = await resources_http_client.fetch_datapool(id)
        datapool_type = make_graphene_type(DatapoolType, datapool_data)
        datapool_type.controller = ControllerType(address=controller_address)
        return datapool_type

    async def resolve_datapools(self, _info, take_broken=False, ordering=None):

        # form list of datapools
        list_of_all_datapool_types = []

        controllers_addresses = await Controller.get_controllers_addresses()
        for controllers_address in controllers_addresses:
            resources_http_client = await ResourcesHttpClient.create(controllers_address)
            datapools = await resources_http_client.fetch_datapool_list(take_broken=take_broken)

            datapool_type_list = await ResourcesQuery.resource_veil_to_graphene_type_list(
                DatapoolType, datapools, controllers_address)
            list_of_all_datapool_types.extend(datapool_type_list)

        # sort list of datapools
        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)

            if ordering == 'verbose_name':
                def sort_lam(datapool): return datapool.verbose_name if datapool.verbose_name else DEFAULT_NAME
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
            list_of_all_datapool_types = sorted(list_of_all_datapool_types, key=sort_lam, reverse=reverse)

        return list_of_all_datapool_types

    async def resolve_requests(self, _info):
        return [
            RequestType(url=None, time=None)
        ]


resources_schema = graphene.Schema(query=ResourcesQuery, auto_camelcase=False)
