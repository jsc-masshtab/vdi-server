# -*- coding: utf-8 -*-
"""Запросы пересылаемые на VeiL ECP по всем контроллерам.

В запросах участвуют только контроллеры в активном статусе.
Запросы привязанные к конкретному контроллеру находятся в схеме контроллера.
"""
import graphene

from veil_api_client import VeilRestPaginator

from yaaredis.exceptions import SerializeError

from common.graphene_utils import ShortString
from common.languages import _local_
from common.log.journal import system_logger
from common.models.controller import Controller, ControllerFetcher
from common.models.pool import Pool
from common.models.vm import Vm
from common.utils import Cache
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SilentError, SimpleError
from common.veil.veil_graphene import (
    VeilResourceType
)

from web_app.cluster_type import ClusterType
from web_app.controller.schema import ControllerType
from web_app.data_pool_type import DataPoolType
from web_app.node_type import NodeType
from web_app.vm_type import VmType


# Resource pool
class ResourcePoolType(VeilResourceType):
    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    description = graphene.Field(ShortString)
    domains_count = graphene.Int()
    memory_limit = graphene.Int()
    cpu_limit = graphene.Int()
    nodes_cpu_count = graphene.Int()
    domains_cpu_count = graphene.Int()
    nodes_memory_count = graphene.Int()
    domains_memory_count = graphene.Int()
    controller = graphene.Field(ControllerType)


class ClusterDataType(graphene.ObjectType):
    clusters = graphene.List(ClusterType)
    count = graphene.Int(default_value=100)


class ResourcePoolDataType(graphene.ObjectType):
    resource_pools = graphene.List(ResourcePoolType)
    count = graphene.Int(default_value=100)


class NodeDataType(graphene.ObjectType):
    nodes = graphene.List(NodeType)
    count = graphene.Int(default_value=100)


class DataPoolDataType(graphene.ObjectType):
    datapools = graphene.List(DataPoolType)
    count = graphene.Int(default_value=100)


class VmDataType(graphene.ObjectType):
    vms = graphene.List(VmType)
    count = graphene.Int(default_value=100)


# Query
class ResourcesQuery(graphene.ObjectType, ControllerFetcher):
    """Данные для вкладки Ресурсы.

    Информация о ресурсах на конкретном контроллере получается в схеме контроллера.
    """

    cluster = graphene.Field(
        ClusterType,
        cluster_id=graphene.UUID(),
        controller_id=graphene.UUID(),
        refresh=graphene.Boolean(default_value=False)
    )
    clusters = graphene.List(
        ClusterType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    clusters_with_count = graphene.Field(
        ClusterDataType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    ###
    resource_pool = graphene.Field(
        ResourcePoolType,
        resource_pool_id=graphene.UUID(),
        controller_id=graphene.UUID(),
        refresh=graphene.Boolean(default_value=False)
    )
    resource_pools = graphene.List(
        ResourcePoolType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    resource_pools_with_count = graphene.Field(
        ResourcePoolDataType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    ###
    node = graphene.Field(
        NodeType,
        node_id=graphene.UUID(),
        controller_id=graphene.UUID(),
        refresh=graphene.Boolean(default_value=False)
    )
    nodes = graphene.List(
        NodeType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    nodes_with_count = graphene.Field(
        NodeDataType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    ###
    datapool = graphene.Field(
        DataPoolType,
        datapool_id=graphene.UUID(),
        controller_id=graphene.UUID(),
        refresh=graphene.Boolean(default_value=False)
    )
    datapools = graphene.List(
        DataPoolType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    datapools_with_count = graphene.Field(
        DataPoolDataType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    ###
    template = graphene.Field(
        VmType,
        template_id=graphene.UUID(),
        controller_id=graphene.UUID(),
        refresh=graphene.Boolean(default_value=False)
    )
    vm = graphene.Field(
        VmType,
        vm_id=graphene.UUID(),
        controller_id=graphene.UUID(),
        refresh=graphene.Boolean(default_value=False)
    )
    templates = graphene.List(
        VmType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    templates_with_count = graphene.Field(
        VmDataType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        refresh=graphene.Boolean(default_value=False)
    )
    vms = templates
    vms_with_count = templates_with_count

    @classmethod
    async def get_resources_list(
        cls, resource_type, limit, offset, ordering: str = None, template: bool = None
    ):
        """Все ресурсы на подключенных ECP VeiL."""
        controllers = await cls.fetch_all()
        resources_list = list()
        total_paginator_count = 0
        for controller in controllers:
            paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
            # Прерываем выполнение при отсутствии клиента
            if not controller.veil_client:
                continue
            # Получаем список для отдельного типа ресурсов
            if resource_type == "cluster":
                veil_response = await controller.veil_client.cluster().list(
                    paginator=paginator
                )
            elif resource_type == "node":
                veil_response = await controller.veil_client.node().list(
                    paginator=paginator
                )
            elif resource_type == "datapool":
                veil_response = await controller.veil_client.data_pool().list(
                    paginator=paginator
                )
            elif resource_type == "resource_pool":
                veil_response = await controller.veil_client.resource_pool().list(
                    paginator=paginator
                )
            # with_vdisks: None - все домены, 0 - только без vdisk'ов, 1 - только с vdisk'ами
            elif resource_type == "domain":
                veil_response = await controller.veil_client.domain(
                    template=template
                ).list(paginator=paginator)
            else:
                raise RuntimeError("unknown resource type")
            total_paginator_count = total_paginator_count + veil_response.paginator_count

            for data in veil_response.response:
                resource = data.public_attrs

                if resource_type == "domain":
                    if data.guest_agent is None:
                        resource["guest_agent"] = data.guest_agent
                    else:
                        resource["guest_agent"] = data.guest_agent.qemu_state
                    resource["hostname"] = data.hostname
                    resource["parent_name"] = data.parent_name

                # Добавляем id, так как в response он не присутствует в чистом виде
                resource["id"] = resource["api_object_id"]
                # Добавляем параметры контроллера на VDI
                resource["controller"] = {
                    "id": controller.id,
                    "verbose_name": controller.verbose_name,
                    "address": controller.address,
                }
                resources_list.append(resource)

        if not ordering:
            resources_list.sort(key=lambda data: data["verbose_name"] or "no name", reverse=True)

        if ordering == "controller":
            resources_list.sort(key=lambda data: data["controller"]["verbose_name"])
        elif ordering == "-controller":
            resources_list.sort(
                key=lambda data: data["controller"]["verbose_name"], reverse=True
            )
        return resources_list, total_paginator_count

    @classmethod
    async def get_resource_data(cls, resource_type, resource_id, controller_id):
        """Получение информации о конкретном ресурсе на контроллере."""
        controller = await cls.fetch_by_id(controller_id)

        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        # Получаем инфо для отдельного типа ресурсов
        if resource_type == "cluster":
            resource_info = await controller.veil_client.cluster(
                cluster_id=str(resource_id)
            ).info()
        elif resource_type == "node":
            resource_info = await controller.veil_client.node(
                node_id=str(resource_id)
            ).info()
        elif resource_type == "datapool":
            resource_info = await controller.veil_client.data_pool(
                data_pool_id=str(resource_id)
            ).info()
        elif resource_type == "resource_pool":
            resource_info = await controller.veil_client.resource_pool(
                resource_pool_id=str(resource_id)
            ).info()
        elif resource_type == "domain":
            resource_info = await controller.veil_client.domain(
                domain_id=str(resource_id)
            ).info()

        if resource_info.success:
            # В случае успеха добавляем параметры контроллера на VDI
            resource_data = resource_info.value
            resource_data["controller"] = {
                "id": str(controller.id),
                "verbose_name": controller.verbose_name,
            }
            return resource_data
        else:
            raise SilentError(
                _local_("{} is unreachable on ECP VeiL.").format(resource_type))

    # Кластеры
    @classmethod
    @administrator_required
    async def resolve_cluster(cls, root, info, creator, cluster_id, controller_id, refresh: bool):
        cache, cache_key, expire_time = await Cache.prepare_cache(cache_key="cluster_cache")
        cache_params = await Cache.get_params(cluster_id, controller_id)

        resource_data = await cache.get(key=cache_key, param=cache_params)
        if not resource_data or refresh:
            resource_data = await cls.get_resource_data(
                resource_type="cluster", resource_id=cluster_id, controller_id=controller_id
            )
            await cache.set(
                key=cache_key, value=resource_data, param=cache_params, expire_time=expire_time
            )
        return ClusterType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_clusters(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        cache, cache_key, expire_time = await Cache.prepare_cache(
            cache_key="clusters_cache", ordering=ordering
        )

        cacheable_clusters_list = await cache.get(cache_key)
        if not cacheable_clusters_list or refresh:
            cacheable_clusters_list = await Cache.get_cacheable_resources_list(
                cache=cache,
                cache_key=cache_key,
                expire_time=expire_time,
                limit=limit,
                offset=offset,
                resource_type="cluster",
                resource_type_class=ClusterType,
                ordering=ordering
            )

        veil_clusters_list = list()
        for resource_data in cacheable_clusters_list:
            veil_clusters_list.append(ClusterType(**resource_data))
        return veil_clusters_list

    @classmethod
    @administrator_required
    async def resolve_clusters_with_count(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        resources_list, total_paginator_count = await ResourcesQuery.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type="cluster"
        )
        gr_type = ClusterDataType()
        gr_type.clusters = resources_list
        gr_type.count = total_paginator_count
        return gr_type

    # Пулы ресурсов
    @classmethod
    @administrator_required
    async def resolve_resource_pool(
        cls, root, info, creator, resource_pool_id, controller_id, refresh: bool
    ):
        cache, cache_key, expire_time = await Cache.prepare_cache(cache_key="resource_pool_cache")
        cache_params = await Cache.get_params(resource_pool_id, controller_id)

        resource_data = await cache.get(key=cache_key, param=cache_params)
        if not resource_data or refresh:
            resource_data = await cls.get_resource_data(
                resource_type="resource_pool",
                resource_id=resource_pool_id,
                controller_id=controller_id,
            )
            await cache.set(
                key=cache_key, value=resource_data, param=cache_params, expire_time=expire_time
            )
        return ResourcePoolType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_resource_pools(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        cache, cache_key, expire_time = await Cache.prepare_cache(
            cache_key="resource_pools_cache", ordering=ordering
        )

        cacheable_resource_pools_list = await cache.get(cache_key)
        if not cacheable_resource_pools_list or refresh:
            cacheable_resource_pools_list = await Cache.get_cacheable_resources_list(
                cache=cache,
                cache_key=cache_key,
                expire_time=expire_time,
                limit=limit,
                offset=offset,
                resource_type="resource_pool",
                resource_type_class=ResourcePoolType,
                ordering=ordering
            )

        veil_resource_pools_list = list()
        for data in cacheable_resource_pools_list:
            veil_resource_pools_list.append(ResourcePoolType(**data))
        return veil_resource_pools_list

    @classmethod
    @administrator_required
    async def resolve_resource_pools_with_count(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        resources_list, total_paginator_count = await ResourcesQuery.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type="resource_pool"
        )
        gr_type = ResourcePoolDataType()
        gr_type.resource_pools = resources_list
        gr_type.count = total_paginator_count
        return gr_type

    # Ноды
    @classmethod
    @administrator_required
    async def resolve_node(cls, root, info, creator, node_id, controller_id, refresh: bool):
        cache, cache_key, expire_time = await Cache.prepare_cache(cache_key="node_cache")
        cache_params = await Cache.get_params(node_id, controller_id)

        resource_data = await cache.get(key=cache_key, param=cache_params)
        if not resource_data or refresh:
            resource_data = await cls.get_resource_data(
                resource_type="node", resource_id=node_id, controller_id=controller_id
            )
            await cache.set(
                key=cache_key, value=resource_data, param=cache_params, expire_time=expire_time
            )
        resource_data["cpu_count"] = resource_data["cpu_topology"]["cpu_count"]
        return NodeType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_nodes(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        cache, cache_key, expire_time = await Cache.prepare_cache(
            cache_key="nodes_cache", ordering=ordering
        )

        cacheable_nodes_list = await cache.get(cache_key)
        if not cacheable_nodes_list or refresh:
            cacheable_nodes_list = await Cache.get_cacheable_resources_list(
                cache=cache,
                cache_key=cache_key,
                expire_time=expire_time,
                limit=limit,
                offset=offset,
                resource_type="node",
                resource_type_class=NodeType,
                ordering=ordering
            )

        veil_nodes_list = list()
        for resource_data in cacheable_nodes_list:
            veil_nodes_list.append(NodeType(**resource_data))
        return veil_nodes_list

    @classmethod
    @administrator_required
    async def resolve_nodes_with_count(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        resources_list, total_paginator_count = await ResourcesQuery.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type="node"
        )
        gr_type = NodeDataType()
        gr_type.nodes = resources_list
        gr_type.count = total_paginator_count
        return gr_type

    # Пулы данных
    @classmethod
    @administrator_required
    async def resolve_datapool(cls, root, info, creator, datapool_id, controller_id, refresh: bool):
        cache, cache_key, expire_time = await Cache.prepare_cache(cache_key="datapool_cache")
        cache_params = await Cache.get_params(datapool_id, controller_id)

        resource_data = await cache.get(key=cache_key, param=cache_params)
        if not resource_data or refresh:
            resource_data = await cls.get_resource_data(
                resource_type="datapool",
                resource_id=datapool_id,
                controller_id=controller_id,
            )
            await cache.set(
                key=cache_key, value=resource_data, param=cache_params, expire_time=expire_time
            )
        return DataPoolType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_datapools(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        cache, cache_key, expire_time = await Cache.prepare_cache(
            cache_key="datapools_cache", ordering=ordering
        )

        cacheable_datapools_list = await cache.get(cache_key)
        if not cacheable_datapools_list or refresh:
            cacheable_datapools_list = await Cache.get_cacheable_resources_list(
                cache=cache,
                cache_key=cache_key,
                expire_time=expire_time,
                limit=limit,
                offset=offset,
                resource_type="datapool",
                resource_type_class=DataPoolType,
                ordering=ordering
            )

        veil_datapools_list = list()
        for resource_data in cacheable_datapools_list:
            veil_datapools_list.append(DataPoolType(**resource_data))
        return veil_datapools_list

    @classmethod
    @administrator_required
    async def resolve_datapools_with_count(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        resources_list, total_paginator_count = await ResourcesQuery.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type="datapool"
        )
        gr_type = DataPoolDataType
        gr_type.datapools = resources_list
        gr_type.count = total_paginator_count
        return gr_type

    # Виртуальные машины и шаблоны
    @classmethod
    async def domain_info(cls, domain_id, controller_id, refresh: bool):
        """Пересылаем запрос на VeiL ECP.

        Даже если отправить template=True, а с таким ID только ВМ - VeiL вернет данные.
        """
        controller = await cls.fetch_by_id(controller_id)
        veil_domain = controller.veil_client.domain(domain_id=str(domain_id))
        await veil_domain.info()

        cache, cache_key, expire_time = await Cache.prepare_cache(cache_key="domain_cache")
        cache_params = await Cache.get_params(domain_id, controller_id)

        resource_data = await cache.get(key=cache_key, param=cache_params)
        if not resource_data or refresh:
            resource_data = await cls.get_resource_data(
                resource_type="domain", resource_id=domain_id, controller_id=controller_id
            )
            await cache.set(
                key=cache_key, value=resource_data, param=cache_params, expire_time=expire_time
            )

        tag_list = await veil_domain.tags_list()
        resource_data["domain_tags"] = list()
        for tag in tag_list.response:
            resource_data["domain_tags"].append(
                {
                    "colour": tag.colour,
                    "verbose_name": tag.verbose_name,
                }
            )
        resource_data["cpu_count"] = veil_domain.cpu_count_prop
        resource_data["parent_name"] = veil_domain.parent_name
        if veil_domain.guest_agent:
            resource_data["guest_agent"] = veil_domain.guest_agent.qemu_state
        if veil_domain.powered:
            resource_data["hostname"] = veil_domain.hostname
            resource_data["address"] = veil_domain.guest_agent.ipv4 if veil_domain.guest_agent else None
        return VmType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_vm(cls, root, info, creator, vm_id, controller_id, refresh: bool):
        """Обёртка для получения информации о ВМ на ECP."""
        return await cls.domain_info(domain_id=vm_id, controller_id=controller_id, refresh=refresh)

    @classmethod
    @administrator_required
    async def resolve_template(cls, root, info, creator, template_id, controller_id, refresh: bool):
        """Обёртка для получения информации о шаблоне ВМ на ECP."""
        return await cls.domain_info(domain_id=template_id, controller_id=controller_id, refresh=refresh)

    @classmethod
    async def domain_list(cls, limit, offset, ordering, template, refresh: bool):
        if template == 0:
            cache_key = "vms_list_cache"
        else:
            cache_key = "templates_list_cache"
        total_paginator_count_key = cache_key + "_total_paginator_count"

        cache, cache_key, expire_time = await Cache.prepare_cache(
            cache_key=cache_key, ordering=ordering
        )

        total_paginator_count = await cache.get(total_paginator_count_key)
        cacheable_domain_list = await cache.get(cache_key)
        if not cacheable_domain_list or refresh:
            domains, total_paginator_count = await cls.get_resources_list(
                limit=limit,
                offset=offset,
                ordering=ordering,
                template=template,
                resource_type="domain",
            )

            for data in domains:
                vm = await Vm.get(data["id"])
                if vm:
                    pool = await Pool.get(vm.pool_id)
                    data["pool_name"] = pool.verbose_name
                else:
                    data["pool_name"] = "--"

            if ordering == "pool_name":
                domains.sort(key=lambda data: data["pool_name"])
            elif ordering == "-pool_name":
                domains.sort(key=lambda data: data["pool_name"], reverse=True)

            cacheable_domain_list = await Cache.get_cacheable_resources(domains, VmType)
            try:
                await cache.set(key=cache_key, value=cacheable_domain_list, expire_time=expire_time)
            except SerializeError:
                pass
            await cache.set(key=total_paginator_count_key, value=total_paginator_count, expire_time=expire_time)

        domain_list = list()
        for resource_data in cacheable_domain_list:
            domain_list.append(VmType(**resource_data))
        return domain_list, total_paginator_count

    @classmethod
    @administrator_required
    async def resolve_vms(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        """Все виртуальные машины на подключенных ECP VeiL."""
        # Для каждого контроллера получаем список всех ВМ за вычетом шаблонов.
        vm_type_list, _ = await cls.domain_list(
            template=0, limit=limit, offset=offset, ordering=ordering, refresh=refresh)

        return vm_type_list

    @classmethod
    @administrator_required
    async def resolve_vms_with_count(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        template_type_list, count = await cls.domain_list(
            template=0, limit=limit, offset=offset, ordering=ordering, refresh=refresh)

        gr_type = VmDataType()
        gr_type.vms = template_type_list
        gr_type.count = count

        return gr_type

    @classmethod
    @administrator_required
    async def resolve_templates(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        """Все шаблоны на подключенных ECP VeiL."""
        # Для каждого контроллера получаем список всех шаблонов за вычетом ВМ.
        template_type_list, _ = await cls.domain_list(
            template=1, limit=limit, offset=offset, ordering=ordering, refresh=refresh)

        return template_type_list

    @classmethod
    @administrator_required
    async def resolve_templates_with_count(
        cls, root, info, creator, limit, offset, refresh: bool, ordering: str = None
    ):
        template_type_list, count = await cls.domain_list(
            template=1, limit=limit, offset=offset, ordering=ordering, refresh=refresh)

        gr_type = VmDataType()
        gr_type.vms = template_type_list
        gr_type.count = count

        return gr_type


class AttachVeilUtilsMutation(graphene.Mutation):
    """Монтирование образа veil utils к ВМ/Шаблону."""

    class Arguments:
        domain_id = graphene.UUID(required=True)
        controller_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    # TODO: code repeat (pool/schema.py)
    @classmethod
    @administrator_required
    async def mutate(cls, root, info, domain_id, controller_id, creator):
        controller = await Controller.get(controller_id)
        veil_domain = controller.veil_client.domain(domain_id=str(domain_id))
        await veil_domain.info()
        if veil_domain.powered:
            raise SilentError(
                _local_("Cant create CD-ROM for powered domain {}.").format(
                    veil_domain.public_attrs["verbose_name"]))
        response = await veil_domain.attach_veil_utils_iso()
        ok = response.success
        if not ok:
            for error in response.errors:
                raise SimpleError(error["detail"])

        await system_logger.info(
            _local_("Creating a CD-ROM on the virtual machine {}.").format(
                veil_domain.public_attrs["verbose_name"]),
            user=creator)
        return AttachVeilUtilsMutation(ok=ok)


class ControllerResourcesMutations(graphene.ObjectType):
    attachVeilUtils = AttachVeilUtilsMutation.Field()


resources_schema = graphene.Schema(
    query=ResourcesQuery, mutation=ControllerResourcesMutations, auto_camelcase=False
)
