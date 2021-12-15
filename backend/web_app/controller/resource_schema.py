# -*- coding: utf-8 -*-
"""Запросы пересылаемые на VeiL ECP по всем контроллерам.

В запросах участвуют только контроллеры в активном статусе.
Запросы привязанные к конкретному контроллеру находятся в схеме контроллера.
"""
import graphene

from veil_api_client import VeilRestPaginator

from common import settings
from common.cache import REDIS_CLIENT, get_params_for_cache
from common.graphene_utils import ShortString
from common.languages import _local_
from common.log.journal import system_logger
from common.models.controller import Controller
from common.models.pool import Pool
from common.models.vm import Vm
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SilentError, SimpleError
from common.veil.veil_gino import StatusGraphene
from common.veil.veil_graphene import (
    VeilResourceType,
    VeilShortEntityType,
    VeilTagsType,
    VmState,
)

from web_app.controller.schema import ControllerFetcher, ControllerType


# Cluster
class ResourceClusterType(VeilResourceType):
    """Описание сущности кластера."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    status = StatusGraphene()
    tags = graphene.List(ShortString)
    hints = graphene.Int()
    built_in = graphene.Boolean()
    cluster_fs_configured = graphene.Boolean()
    controller = graphene.Field(VeilShortEntityType)
    anti_affinity_enabled = graphene.Boolean()
    datacenter = graphene.Field(VeilShortEntityType)
    ha_autoselect = graphene.Boolean()
    quorum = graphene.Boolean()
    drs_strategy = graphene.Boolean()
    cpu_count = graphene.Int()
    cluster_fs_type = graphene.Field(ShortString)
    ha_timeout = graphene.Int()
    drs_check_timeout = graphene.Int()
    drs_deviation_limit = graphene.Float()
    nodes = graphene.List(VeilShortEntityType)
    nodes_count = graphene.Int()
    memory_count = graphene.Int()
    description = graphene.Field(ShortString)
    ha_retrycount = graphene.Int()
    drs_mode = graphene.Field(ShortString)
    drs_metrics_strategy = graphene.Field(ShortString)


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


# Node aka Server
class ResourceNodeType(VeilResourceType):
    """Описание ноды на ECP VeiL."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    status = StatusGraphene()
    domains_count = graphene.Int()
    management_ip = graphene.Field(ShortString)
    domains_on_count = graphene.Int()
    datacenter_name = graphene.Field(ShortString)
    cluster = graphene.Field(VeilShortEntityType)
    memory_count = graphene.Int()
    datacenter_id = graphene.UUID()
    built_in = graphene.Boolean()
    cpu_count = graphene.Int()
    hints = graphene.Int()
    tags = graphene.List(ShortString)
    controller = graphene.Field(VeilShortEntityType)
    version = graphene.Field(ShortString)
    ksm_pages_to_scan = graphene.Int()
    ballooning = graphene.Boolean()
    cluster_name = graphene.Field(ShortString)
    description = graphene.Field(ShortString)
    node_plus_controller_installation = graphene.Boolean()
    heartbeat_type = graphene.Field(ShortString)
    ipmi_username = graphene.Field(ShortString)
    ksm_merge_across_nodes = graphene.Int()
    datacenter_name = graphene.Field(ShortString)
    fencing_type = graphene.Field(ShortString)
    ksm_enable = graphene.Int()
    ksm_sleep_time = graphene.Int()


# Datapool
class ResourceDataPoolType(VeilResourceType):
    """Описание пула-данных на ECP VeiL."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    description = graphene.Field(ShortString)
    status = StatusGraphene()
    controller = graphene.Field(VeilShortEntityType)
    tags = graphene.List(ShortString)
    hints = graphene.Int()
    built_in = graphene.Boolean()
    free_space = graphene.Int()
    used_space = graphene.Int()
    vdisk_count = graphene.Int()
    type = graphene.Field(ShortString)
    file_count = graphene.Int()
    size = graphene.Int()
    iso_count = graphene.Int()
    nodes_connected = graphene.List(VeilShortEntityType)
    zfs_pool = graphene.UUID()
    shared_storage = graphene.Field(VeilShortEntityType)
    cluster_storage = graphene.Field(VeilShortEntityType)
    lun = graphene.JSONString()
    options = graphene.JSONString()


# VM aka Domain
class ResourceVmType(VeilResourceType):
    """Описание ВМ на ECP VeiL."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    status = StatusGraphene()
    controller = graphene.Field(VeilShortEntityType)
    resource_pool = graphene.Field(VeilShortEntityType)
    memory_count = graphene.Int()
    cpu_count = graphene.Int()
    template = graphene.Boolean()
    tags = graphene.List(ShortString)
    hints = graphene.Int()
    user_power_state = VmState()
    safety = graphene.Boolean()
    boot_type = graphene.Field(ShortString)
    start_on_boot = graphene.Boolean()
    cloud_init = graphene.Boolean()
    disastery_enabled = graphene.Boolean()
    thin = graphene.Boolean()
    ha_retrycount = graphene.Boolean()
    ha_timeout = graphene.Int()
    ha_enabled = graphene.Boolean()
    clean_type = graphene.Field(ShortString)
    machine = graphene.Field(ShortString)
    graphics_password = graphene.Field(ShortString)
    remote_access = graphene.Boolean()
    bootmenu_timeout = graphene.Int()
    os_type = graphene.Field(ShortString)
    cpu_type = graphene.Field(ShortString)
    description = graphene.Field(ShortString)
    guest_agent = graphene.Boolean()
    os_version = graphene.Field(ShortString)
    spice_stream = graphene.Boolean()
    tablet = graphene.Boolean()
    parent = graphene.Field(VeilShortEntityType)
    parent_name = graphene.Field(ShortString)
    hostname = graphene.Field(ShortString)
    address = graphene.List(ShortString)
    domain_tags = graphene.List(VeilTagsType)

    # название пула, в котором ВМ из локальной БД
    pool_name = graphene.Field(ShortString)


# Query
class ResourcesQuery(graphene.ObjectType, ControllerFetcher):
    """Данные для вкладки Ресурсы.

    Информация о ресурсах на конкретном контроллере получается в схеме контроллера.
    """

    cluster = graphene.Field(
        ResourceClusterType, cluster_id=graphene.UUID(), controller_id=graphene.UUID()
    )
    clusters = graphene.List(
        ResourceClusterType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )

    resource_pool = graphene.Field(
        ResourcePoolType,
        resource_pool_id=graphene.UUID(),
        controller_id=graphene.UUID(),
    )
    resource_pools = graphene.List(
        ResourcePoolType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )

    node = graphene.Field(
        ResourceNodeType, node_id=graphene.UUID(), controller_id=graphene.UUID()
    )
    nodes = graphene.List(
        ResourceNodeType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )

    datapool = graphene.Field(
        ResourceDataPoolType, datapool_id=graphene.UUID(), controller_id=graphene.UUID()
    )
    datapools = graphene.List(
        ResourceDataPoolType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )

    template = graphene.Field(
        ResourceVmType, template_id=graphene.UUID(), controller_id=graphene.UUID()
    )
    vm = graphene.Field(
        ResourceVmType, vm_id=graphene.UUID(), controller_id=graphene.UUID()
    )
    templates = graphene.List(
        ResourceVmType,
        ordering=ShortString(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )
    vms = templates

    @classmethod
    async def get_resources_list(
        cls, resource_type, limit, offset, ordering: str = None, template: bool = None
    ):
        """Все ресурсы на подключенных ECP VeiL."""
        controllers = await cls.fetch_all()
        resources_list = list()
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

            for data in veil_response.response:
                resource = data.public_attrs
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
            resources_list.sort(key=lambda data: data["verbose_name"], reverse=True)

        if ordering == "controller":
            resources_list.sort(key=lambda data: data["controller"]["verbose_name"])
        elif ordering == "-controller":
            resources_list.sort(
                key=lambda data: data["controller"]["verbose_name"], reverse=True
            )

        return resources_list

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
    async def resolve_cluster(cls, root, info, creator, cluster_id, controller_id):
        cache_key = "cluster_cache"
        cache = REDIS_CLIENT.cache(cache_key)
        cache_params = get_params_for_cache(cluster_id, controller_id)

        resource_data = await cache.get(cache_key, cache_params)
        if not resource_data:
            resource_data = await cls.get_resource_data(
                resource_type="cluster", resource_id=cluster_id, controller_id=controller_id
            )
            await cache.set(
                cache_key, resource_data, cache_params, expire_time=settings.REDIS_EXPIRE_TIME
            )
        return ResourceClusterType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_clusters(
        cls, root, info, creator, limit, offset, ordering: str = None
    ):
        clusters_list = await cls.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type="cluster"
        )
        veil_clusters_list = list()
        for resource_data in clusters_list:
            veil_clusters_list.append(ResourceClusterType(**resource_data))
        return veil_clusters_list

    # Пулы ресурсов
    @classmethod
    @administrator_required
    async def resolve_resource_pool(
        cls, root, info, creator, resource_pool_id, controller_id
    ):
        cache_key = "resource_pool_cache"
        cache = REDIS_CLIENT.cache(cache_key)
        cache_params = get_params_for_cache(resource_pool_id, controller_id)

        resource_data = await cache.get(cache_key, cache_params)
        if not resource_data:
            resource_data = await cls.get_resource_data(
                resource_type="resource_pool",
                resource_id=resource_pool_id,
                controller_id=controller_id,
            )
            await cache.set(
                cache_key, resource_data, cache_params, expire_time=settings.REDIS_EXPIRE_TIME
            )
        return ResourcePoolType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_resource_pools(
        cls, root, info, creator, limit, offset, ordering: str = None
    ):
        resource_pools_list = await cls.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type="resource_pool"
        )
        veil_resource_pools_list = list()
        for data in resource_pools_list:
            veil_resource_pools_list.append(ResourcePoolType(**data))
        return veil_resource_pools_list

    # Ноды
    @classmethod
    @administrator_required
    async def resolve_node(cls, root, info, creator, node_id, controller_id):
        cache_key = "node_cache"
        cache = REDIS_CLIENT.cache(cache_key)
        cache_params = get_params_for_cache(node_id, controller_id)

        resource_data = await cache.get(cache_key, cache_params)
        if not resource_data:
            resource_data = await cls.get_resource_data(
                resource_type="node", resource_id=node_id, controller_id=controller_id
            )
            await cache.set(
                cache_key, resource_data, cache_params, expire_time=settings.REDIS_EXPIRE_TIME
            )
        resource_data["cpu_count"] = resource_data["cpu_topology"]["cpu_count"]
        return ResourceNodeType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_nodes(
        cls, root, info, creator, limit, offset, ordering: str = None
    ):
        nodes_list = await cls.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type="node"
        )
        veil_nodes_list = list()
        for resource_data in nodes_list:
            veil_nodes_list.append(ResourceNodeType(**resource_data))
        return veil_nodes_list

    # Пулы данных
    @classmethod
    @administrator_required
    async def resolve_datapool(cls, root, info, creator, datapool_id, controller_id):
        cache_key = "datapool_cache"
        cache = REDIS_CLIENT.cache(cache_key)
        cache_params = get_params_for_cache(datapool_id, controller_id)

        resource_data = await cache.get(cache_key, cache_params)
        if not resource_data:
            resource_data = await cls.get_resource_data(
                resource_type="datapool",
                resource_id=datapool_id,
                controller_id=controller_id,
            )
            await cache.set(
                cache_key, resource_data, cache_params, expire_time=settings.REDIS_EXPIRE_TIME
            )
        return ResourceDataPoolType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_datapools(
        cls, root, info, creator, limit, offset, ordering: str = None
    ):
        datapools_list = await cls.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type="datapool"
        )
        veil_datapools_list = list()
        for resource_data in datapools_list:
            veil_datapools_list.append(ResourceDataPoolType(**resource_data))
        return veil_datapools_list

    # Виртуальные машины и шаблоны
    @classmethod
    async def domain_info(cls, domain_id, controller_id):
        """Пересылаем запрос на VeiL ECP.

        Даже если отправить template=True, а с таким ID только ВМ - VeiL вернет данные.
        """
        controller = await cls.fetch_by_id(controller_id)
        veil_domain = controller.veil_client.domain(domain_id=str(domain_id))
        await veil_domain.info()

        cache_key = "domain_cache"
        cache = REDIS_CLIENT.cache(cache_key)
        cache_params = get_params_for_cache(domain_id, controller_id)

        resource_data = await cache.get(cache_key, cache_params)
        if not resource_data:
            resource_data = await cls.get_resource_data(
                resource_type="domain", resource_id=domain_id, controller_id=controller_id
            )
            await cache.set(
                cache_key, resource_data, cache_params, expire_time=settings.REDIS_EXPIRE_TIME
            )

        tag_list = await veil_domain.tags_list()
        resource_data["domain_tags"] = list()
        for tag in tag_list.response:
            resource_data["domain_tags"].append(
                {
                    "colour": tag.colour,
                    "verbose_name": tag.verbose_name,
                    "slug": tag.slug,
                }
            )
        resource_data["cpu_count"] = veil_domain.cpu_count_prop
        resource_data["parent_name"] = veil_domain.parent_name
        if veil_domain.guest_agent:
            resource_data["guest_agent"] = veil_domain.guest_agent.qemu_state
        if veil_domain.powered:
            resource_data["hostname"] = veil_domain.hostname
            resource_data["address"] = veil_domain.guest_agent.ipv4
        return ResourceVmType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_vm(cls, root, info, creator, vm_id, controller_id):
        """Обёртка для получения информации о ВМ на ECP."""
        return await cls.domain_info(domain_id=vm_id, controller_id=controller_id)

    @classmethod
    @administrator_required
    async def resolve_template(cls, root, info, creator, template_id, controller_id):
        """Обёртка для получения информации о шаблоне ВМ на ECP."""
        return await cls.domain_info(domain_id=template_id, controller_id=controller_id)

    @classmethod
    async def domain_list(cls, limit, offset, ordering, template: bool):
        domains = await cls.get_resources_list(
            limit=limit,
            offset=offset,
            ordering=ordering,
            template=template,
            resource_type="domain",
        )
        domain_list = list()

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

        for resource_data in domains:
            domain_list.append(ResourceVmType(**resource_data))
        return domain_list

    @classmethod
    @administrator_required
    async def resolve_vms(
        cls, root, info, creator, limit, offset, ordering: str = None
    ):
        """Все виртуальные машины на подключенных ECP VeiL."""
        # Для каждого контроллера получаем список всех ВМ за вычетом шаблонов.
        vm_type_list = await cls.domain_list(
            template=0, limit=limit, offset=offset, ordering=ordering
        )

        return vm_type_list

    @classmethod
    @administrator_required
    async def resolve_templates(
        cls, root, info, creator, limit, offset, ordering: str = None
    ):
        """Все шаблоны на подключенных ECP VeiL."""
        # Для каждого контроллера получаем список всех шаблонов за вычетом ВМ.
        template_type_list = await cls.domain_list(
            template=1, limit=limit, offset=offset, ordering=ordering
        )

        return template_type_list


class AttachVeilUtilsMutation(graphene.Mutation):
    """Монтирование образа veil utils к ВМ/Шаблону."""

    class Arguments:
        domain_id = graphene.UUID(required=True)
        controller_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

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
