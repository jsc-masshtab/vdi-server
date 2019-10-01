import asyncio
from async_generator import async_generator, yield_, asynccontextmanager
from rx import Observable

import graphene
from classy_async.classy_async import wait

from .pool import PoolType, VmType, TemplateType
from .util import get_selections, make_resource_type
from db.db import db
from ..tasks import Token
from ..tasks.vm import ListTemplates, ListVms

from ..tasks.resources import (
    DiscoverControllers, FetchNode, FetchCluster, DiscoverControllerIp, ListClusters,
    ListDatapools, ListNodes, FetchResourcesUsage, CheckController, DiscoverControllerIpByCluster
)

from vdi.errors import FieldError, SimpleError, FetchException
from vdi.utils import Unset
from vdi.utils import clamp_value

from vdi.resources_monitoring.resources_monitor_manager import resources_monitor_manager


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

    async def resolve_nodes(self, info):
        return await self.controller.resolve_nodes(info, cluster_id=self.id)

    async def resolve_templates(self, info):
        return await self.controller.resolve_templates(info, cluster_id=self.id)

    async def resolve_datapools(self, info):
        return await self.controller.resolve_datapools(info, cluster_id=self.id)

    async def resolve_vms(self, info, wild=True):
        return await self.controller.resolve_vms(info, cluster_id=self.id, wild=wild)

    async def resolve_resources_usage(self, _info):
        return await FetchResourcesUsage(controller_ip=self.controller.ip,
                                         resource_category_name='clusters', resource_id=self.id)


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
    resources_usage = graphene.Field(ResourcesUsageType)

    veil_info = Unset  # dict

    async def get_veil_info(self):
        return await FetchNode(node_id=self.id, controller_ip=self.controller.ip)

    async def resolve_verbose_name(self, info):
        if self.verbose_name:
            return self.verbose_name
        if self.veil_info is Unset:
            veil_info = await self.get_veil_info()
        return veil_info['verbose_name']

    async def resolve_templates(self, info):
        return await self.controller.resolve_templates(info, node_id=self.id)

    async def resolve_datapools(self, info):
        return await self.controller.resolve_datapools(info, node_id=self.id)

    async def resolve_vms(self, info, wild=True):
        return await self.controller.resolve_vms(info, node_id=self.id, wild=wild)

    async def resolve_cluster(self, info):
        if self.veil_info is Unset:
            self.veil_info = await self.get_veil_info()
        cluster_id = self.veil_info['cluster']['id']
        #TODO return immediately
        resp = await FetchCluster(controller_ip=self.controller.ip, cluster_id=cluster_id)
        obj = make_resource_type(ClusterType, resp)
        obj.controller = self.controller
        return obj

    async def resolve_datacenter(self, info):
        if self.datacenter:
            return self.datacenter
        if self.veil_info is Unset:
            self.veil_info = await self.get_veil_info()
        return DatacenterType(id=self.veil_info['datacenter_id'],
                              verbose_name=self.veil_info['datacenter_name'])

    async def resolve_resources_usage(self, _info):
        return await FetchResourcesUsage(controller_ip=self.controller.ip,
                                         resource_category_name='nodes', resource_id=self.id)


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
                FetchNode(controller_ip=self.controller_ip, node_id=node['id'])
                for node in self.nodes
            ]
            async for node in wait(*tasks):
                obj = make_resource_type(NodeType, node)
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



class Resources:
    controllers = graphene.List(lambda: ControllerType)
    controller = graphene.Field(lambda: ControllerType, ip=graphene.String())
    node = graphene.Field(NodeType, id=graphene.String())
    cluster = graphene.Field(ClusterType, id=graphene.String())
    datapool = graphene.Field(DatapoolType, id=graphene.String())
    template = graphene.Field(TemplateType, id=graphene.String())
    vm = graphene.Field(VmType, id=graphene.String())

    requests = graphene.List(RequestType, time=graphene.Float())

    @staticmethod
    async def get_all_known_controller_ips():
        async with db.connect() as conn:
            sql_query = "SELECT ip FROM controller"
            controllers_ips = await conn.fetch(sql_query)
        return controllers_ips

    @staticmethod
    async def get_resource(_info, id, resource_type, function_to_get_resource_list, fields_map={}):
        # get all known controller ips
        controllers_ips = await Resources.get_all_known_controller_ips()

        # find out on which controller our resource is
        for controllers_ip in controllers_ips:
            # try to get list of resources
            try:
                resource_list = await function_to_get_resource_list(controller_ip=controllers_ip['ip'])
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

    async def resolve_controllers(self, info):
        objects = [
            ControllerType(**item)
            for item in await DiscoverControllers()
        ]
        return objects

    async def resolve_controller(self, _info, ip):
        # find controller info by ip
        connected_controllers = await DiscoverControllers(return_broken=False)
        try:
            controller_info = next(controller_info
                for controller_info in connected_controllers if controller_info['ip'] == ip)
            return ControllerType(**controller_info)
        except StopIteration:
            raise FieldError(id=['Контроллер с заданным ip недоступен'])

    async def resolve_node(self, info, id):
        controller_ip = await DiscoverControllerIp(node_id=id)
        if not controller_ip:
            raise SimpleError('Узел с данным id не найден')
        # Node exists for sure
        data = await FetchNode(controller_ip=controller_ip, node_id=id)
        fields = {
            k: v for k, v in data.items()
            if k in NodeType._meta.fields
        }
        return NodeType(controller=ControllerType(ip=controller_ip), **fields)

    async def resolve_cluster(self, _info, id):
        controllers_ips = await Resources.get_all_known_controller_ips()
        for controller_ip in controllers_ips:
            # try to get list of resources
            try:
                data = await FetchCluster(controller_ip=controller_ip['ip'], cluster_id=id)
                fields = {
                    k: v for k, v in data.items()
                    if k in ClusterType._meta.fields
                }
                return ClusterType(controller=ControllerType(ip=controller_ip['ip']), **fields)
            except:
                continue

        return None

    async def resolve_datapool(self, _info, id):
        datapool = await Resources.get_resource(_info, id, DatapoolType, ListDatapools)
        return datapool

    async def resolve_template(self, _info, id):
        template = await Resources.get_resource(_info, id, TemplateType, ListTemplates, {'verbose_name': 'name'})
        return template

    async def resolve_vm(self, _info, id):
        vm = await Resources.get_resource(_info, id, VmType, ListVms)
        return vm

    async def resolve_requests(self, info):
        return [
            RequestType(url=None, time=None)
        ]


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
            resp = await ListClusters(controller_ip=ip)
        except FetchException:
            return AddController(ok=False)

        async with db.connect() as conn:
            query = '''
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
        # add controller to resources_monitor_manager
        resources_monitor_manager.add_controller(ip)
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

        from vdi.graphql_api.pool import RemovePool
        tasks = [
            RemovePool.do_remove(pool['id'])
            for pool in pools
        ]
        async for _ in wait(*tasks):
            pass


    async def mutate(self, info, controller_ip):
        async with db.connect() as conn:
            await RemoveController._remove_pools(controller_ip=controller_ip)
            query = "DELETE FROM default_controller WHERE ip = $1", controller_ip
            await conn.fetch(*query)
            query = "DELETE FROM controller WHERE ip=$1", controller_ip
            await conn.execute(*query)

        # remove controller from resources_monitor_manager
        resources_monitor_manager.remove_controller(controller_ip)
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
                              cluster_id=graphene.String(),
                              take_broken=graphene.Boolean())
    clusters = graphene.List(ClusterType)
    cluster = graphene.Field(ClusterType, id=graphene.String())
    nodes = graphene.List(NodeType, cluster_id=graphene.String())
    node = graphene.Field(NodeType, id=graphene.String())

    is_online = graphene.Boolean()


    async def resolve_templates(self, info, cluster_id=None, node_id=None):
        if node_id is not None:
            nodes = {node_id}
        elif cluster_id is not None:
            nodes = await ListNodes(controller_ip=self.ip, cluster_id=cluster_id)
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
            obj = TemplateType(name=vm['verbose_name'], veil_info=vm, id=vm['id'], node=node)
            obj.controller_ip = self.ip
            objects.append(obj)
        return objects

    async def resolve_vms(self, info, cluster_id=None, node_id=None, wild=True):
        if node_id is not None:
            nodes = {node_id}
        elif cluster_id is not None:
            nodes = await ListNodes(controller_ip=self.ip, cluster_id=cluster_id)
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
        async with db.connect() as conn:
            qu = "select id, pool_id from vm where id = any($1::text[])", list(vm_ids)
            data = await conn.fetch(*qu)
            for item in data:
                id = item['id']
                vm_ids[id] = item['pool_id']

        if not wild:
            vm_ids = {k: v for k, v in vm_ids.items() if v is not None}

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
            obj.veil_info = vm
            if not pool_id:
                obj.controller_ip = self.ip

            objects.append(obj)
        return objects


    async def resolve_datapools(self, info, node_id=None, cluster_id=None, take_broken=False):
        controller_ip = self.ip
        if node_id is not None:
            return self._get_datapools(info, node_id=node_id, take_broken=take_broken)
        if cluster_id is not None:
            cluster_ids = [cluster_id]
        else:
            clusters = await ListClusters(controller_ip=controller_ip)
            cluster_ids = [c['id'] for c in clusters]
        datapools = {}

        for cluster_id in cluster_ids:
            nodes = await ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
            for node in nodes:
                objects = await self._get_datapools(info, node_id=node['id'], take_broken=take_broken)
                datapools.update(
                    (obj.id, obj) for obj in objects
                )
        datapools = list(datapools.values())
        return datapools

    # TODO fields/info rework

    async def _get_datapools(self, info, node_id, take_broken=False):
        resp = await ListDatapools(controller_ip=self.ip, node_id=node_id, take_broken=take_broken)
        fields = get_selections(info)

        li = []
        for item in resp:
            obj = make_resource_type(DatapoolType, item, {'nodes_connected': 'nodes'})
            obj.controller_ip = self.ip
            li.append(obj)

        return li

    async def resolve_clusters(self, info):
        controller_ip = self.ip
        resp = await ListClusters(controller_ip)
        li = []
        for item in resp:
            obj = make_resource_type(ClusterType, item)
            obj.controller = self
            obj.nodes = []
            li.append(obj)
        return li

    async def resolve_cluster(self, info, *, id):
        controller_ip = self.ip
        resp = await FetchCluster(controller_ip=controller_ip, cluster_id=id)
        obj = make_resource_type(ClusterType, resp)
        obj.controller = self
        return obj

    async def _get_nodes(self, info, *, cluster_id):
        nodes = await ListNodes(controller_ip=self.ip, cluster_id=cluster_id)
        li = []
        for node in nodes:
            obj = make_resource_type(NodeType, node)
            obj.controller = self
            li.append(obj)
        return li

    async def resolve_nodes(self, info, cluster_id=None):
        controller_ip = self.ip
        if cluster_id is not None:
            return await self._get_nodes(info, cluster_id=cluster_id)
        result = {}
        clusters = await ListClusters(controller_ip=controller_ip)
        for cluster in clusters:
            nodes = await self._get_nodes(info, cluster_id=cluster['id'])
            result.update(
                (obj.id, obj) for obj in nodes
            )
        return list(result.values())

    async def resolve_node(self, info, id):
        controller_ip = self.ip
        node = await FetchNode(controller_ip=controller_ip, node_id=id)
        obj = make_resource_type(NodeType, node)
        obj.controller = self
        return obj

    async def resolve_is_online(self, _info):
        try:
            await CheckController(controller_ip=self.ip)
        except:
            return False
        else:
            return True

# remove later
class TestSubscription(graphene.ObjectType):
    # count_seconds = graphene.Float(up_to=graphene.Int())
    #
    # @async_generator
    # async def resolve_count_seconds(root, _info, up_to):
    #     for i in range(up_to):
    #         await yield_(i)
    #         await asyncio.sleep(1.)
    #     await yield_(up_to)
    count_seconds = graphene.Float(up_to=graphene.Int())

    async def resolve_count_seconds(root, info, up_to=5):
        return Observable.interval(1000) \
            .map(lambda i: "{0}".format(i)) \
            .take_while(lambda i: int(i) <= up_to)


class ResourceDataSubscription(graphene.ObjectType):

    cluster_res_usage = graphene.Field(ResourcesUsageType, cluster_id=graphene.ID(), timeout=graphene.Int())
    node_res_usage = graphene.Field(ResourcesUsageType, node_id=graphene.ID(), timeout=graphene.Int())
    is_controller_online = graphene.Boolean(controller_ip=graphene.String(), timeout=graphene.Int())

    @staticmethod
    async def _sleep(timeout):
        adequate_timeout = clamp_value(timeout, 1, 1000)
        await asyncio.sleep(adequate_timeout)

    @async_generator
    async def resolve_cluster_res_usage(self, _info, cluster_id, timeout=2):

        controller_ip = await DiscoverControllerIp(cluster_id=cluster_id)
        while True:
            res_usage = await FetchResourcesUsage(controller_ip=controller_ip,
                                                  resource_category_name='clusters', resource_id=cluster_id)
            await yield_(res_usage)
            await ResourceDataSubscription._sleep(timeout)

    @async_generator
    async def resolve_node_res_usage(self, _info, node_id, timeout=2):

        controller_ip = await DiscoverControllerIp(node_id=node_id)
        while True:
            res_usage = await FetchResourcesUsage(controller_ip=controller_ip,
                                                  resource_category_name='nodes', resource_id=node_id)
            await yield_(res_usage)
            await ResourceDataSubscription._sleep(timeout)

    @async_generator
    async def resolve_is_controller_online(self, _info, controller_ip, timeout=2):
        while True:
            was_exception = False
            try:
                await CheckController(controller_ip=controller_ip)
            except:  # wat excep type
                was_exception = True

            await yield_(not was_exception)
            await ResourceDataSubscription._sleep(timeout)
