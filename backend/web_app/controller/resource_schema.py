# -*- coding: utf-8 -*-
"""Запросы пересылаемые на VeiL ECP по всем контроллерам.

В запросах участвуют только контроллеры в активном статусе.
Запросы привязанные к конкретному контроллеру находятся в схеме контроллера.
"""

import graphene

from common.veil.veil_decorators import administrator_required
from common.veil.veil_graphene import VeilResourceType, VmState, VeilShortEntityType, VeilTagsType
from common.veil.veil_gino import StatusGraphene
from common.veil.veil_errors import SilentError
from veil_api_client import VeilRestPaginator
from web_app.controller.schema import ControllerFetcher, ControllerType
from common.languages import lang_init
from common.models.vm import Vm
from common.models.pool import Pool

_ = lang_init()


# Cluster
class ResourceClusterType(VeilResourceType):
    """Описание сущности кластера."""

    id = graphene.UUID()
    verbose_name = graphene.String()
    status = StatusGraphene()
    tags = graphene.List(graphene.String)
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
    cluster_fs_type = graphene.String()
    ha_timeout = graphene.Int()
    drs_check_timeout = graphene.Int()
    drs_deviation_limit = graphene.Float()
    nodes = graphene.List(VeilShortEntityType)
    nodes_count = graphene.Int()
    memory_count = graphene.Int()
    description = graphene.String()
    ha_retrycount = graphene.Int()
    drs_mode = graphene.String()
    drs_metrics_strategy = graphene.String()


# Resource pool
class ResourcePoolType(VeilResourceType):
    id = graphene.UUID()
    verbose_name = graphene.String()
    description = graphene.String()
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
    verbose_name = graphene.String()
    status = StatusGraphene()
    domains_count = graphene.Int()
    management_ip = graphene.String()
    domains_on_count = graphene.Int()
    datacenter_name = graphene.String()
    cluster = graphene.Field(VeilShortEntityType)
    memory_count = graphene.Int()
    datacenter_id = graphene.UUID()
    built_in = graphene.Boolean()
    cpu_count = graphene.Int()
    hints = graphene.Int()
    tags = graphene.List(graphene.String)
    controller = graphene.Field(VeilShortEntityType)
    version = graphene.String()
    ksm_pages_to_scan = graphene.Int()
    ballooning = graphene.Boolean()
    cluster_name = graphene.String()
    description = graphene.String()
    node_plus_controller_installation = graphene.Boolean()
    heartbeat_type = graphene.String()
    ipmi_username = graphene.String()
    ksm_merge_across_nodes = graphene.Int()
    datacenter_name = graphene.String()
    fencing_type = graphene.String()
    ksm_enable = graphene.Int()
    ksm_sleep_time = graphene.Int()


# Datapool
class ResourceDataPoolType(VeilResourceType):
    """Описание пула-данных на ECP VeiL."""

    id = graphene.UUID()
    verbose_name = graphene.String()
    status = StatusGraphene()
    controller = graphene.Field(VeilShortEntityType)
    tags = graphene.List(graphene.String)
    hints = graphene.Int()
    built_in = graphene.Boolean()
    free_space = graphene.Int()
    used_space = graphene.Int()
    vdisk_count = graphene.Int()
    type = graphene.String()
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
    verbose_name = graphene.String()
    status = StatusGraphene()
    controller = graphene.Field(VeilShortEntityType)
    resource_pool = graphene.Field(VeilShortEntityType)
    memory_count = graphene.Int()
    cpu_count = graphene.Int()
    template = graphene.Boolean()
    # luns_count = graphene.Int()
    # vfunctions_count = graphene.Int()
    tags = graphene.List(graphene.String)
    # vmachine_infs_count = graphene.Int()
    hints = graphene.Int()
    user_power_state = VmState()
    # vdisks_count = graphene.Int()
    safety = graphene.Boolean()
    boot_type = graphene.String()
    start_on_boot = graphene.Boolean()
    cloud_init = graphene.Boolean()
    disastery_enabled = graphene.Boolean()
    thin = graphene.Boolean()
    ha_retrycount = graphene.Boolean()
    ha_timeout = graphene.Int()
    ha_enabled = graphene.Boolean()
    clean_type = graphene.String()
    machine = graphene.String()
    graphics_password = graphene.String()
    remote_access = graphene.Boolean()
    bootmenu_timeout = graphene.Int()
    os_type = graphene.String()
    cpu_type = graphene.String()
    description = graphene.String()
    guest_agent = graphene.Boolean()
    os_version = graphene.String()
    spice_stream = graphene.Boolean()
    tablet = graphene.Boolean()
    parent = graphene.Field(VeilShortEntityType)
    parent_name = graphene.String()
    hostname = graphene.String()
    address = graphene.List(graphene.String)
    domain_tags = graphene.List(VeilTagsType)

    # название пула, в котором ВМ из локальной БД
    pool_name = graphene.String()


# Query
class ResourcesQuery(graphene.ObjectType, ControllerFetcher):
    """Данные для вкладки Ресурсы.

    Информация о ресурсах на конкретном контроллере получается в схеме контроллера.
    """

    # TODO: унифицировать преобразование данных ответа в класс
    cluster = graphene.Field(ResourceClusterType, cluster_id=graphene.UUID(), controller_id=graphene.UUID())
    clusters = graphene.List(ResourceClusterType, ordering=graphene.String(), limit=graphene.Int(default_value=100),
                             offset=graphene.Int(default_value=0))

    resource_pool = graphene.Field(ResourcePoolType, resource_pool_id=graphene.UUID(), controller_id=graphene.UUID())
    resource_pools = graphene.List(ResourcePoolType, ordering=graphene.String(), limit=graphene.Int(default_value=100),
                                   offset=graphene.Int(default_value=0))

    node = graphene.Field(ResourceNodeType, node_id=graphene.UUID(), controller_id=graphene.UUID())
    nodes = graphene.List(ResourceNodeType, ordering=graphene.String(), limit=graphene.Int(default_value=100),
                          offset=graphene.Int(default_value=0))

    datapool = graphene.Field(ResourceDataPoolType, datapool_id=graphene.UUID(), controller_id=graphene.UUID())
    datapools = graphene.List(ResourceDataPoolType, ordering=graphene.String(), limit=graphene.Int(default_value=100),
                              offset=graphene.Int(default_value=0))

    template = graphene.Field(ResourceVmType, template_id=graphene.UUID(), controller_id=graphene.UUID())
    vm = graphene.Field(ResourceVmType, vm_id=graphene.UUID(), controller_id=graphene.UUID())
    templates = graphene.List(ResourceVmType, ordering=graphene.String(), limit=graphene.Int(default_value=100),
                              offset=graphene.Int(default_value=0))
    vms = templates

    # Кластеры
    @classmethod
    @administrator_required
    async def resolve_cluster(cls, root, info, creator, cluster_id, controller_id):
        """Получение информации о конкретном кластере на контроллере."""
        controller = await cls.fetch_by_id(controller_id)

        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        cluster_info = await controller.veil_client.cluster(cluster_id=str(cluster_id)).info()
        resource_data = cluster_info.value
        resource_data['controller'] = {'id': controller.id, 'verbose_name': controller.verbose_name}
        return ResourceClusterType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_clusters(cls, root, info, creator, limit, offset, ordering: str = None):
        """Все кластеры на подключенных ECP VeiL."""
        controllers = await cls.fetch_all()
        veil_clusters_list = list()
        clusters_list = list()
        for controller in controllers:
            paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
            # Прерываем выполнение при отсутствии клиента
            if not controller.veil_client:
                continue
            veil_response = await controller.veil_client.cluster().list(paginator=paginator)
            for cluster in veil_response.paginator_results:
                # Добавляем параметры контроллера на VDI
                cluster['controller'] = {'id': controller.id, 'verbose_name': controller.verbose_name}
                clusters_list.append(cluster)

        if not ordering:
            clusters_list.sort(key=lambda data: data['verbose_name'], reverse=True)

        if ordering == 'controller':
            clusters_list.sort(key=lambda data: data['controller']['verbose_name'])
        elif ordering == '-controller':
            clusters_list.sort(key=lambda data: data['controller']['verbose_name'], reverse=True)

        for resource_data in clusters_list:
            veil_clusters_list.append(ResourceClusterType(**resource_data))

        return veil_clusters_list

    # Пулы ресурсов
    @classmethod
    @administrator_required
    async def resolve_resource_pool(cls, root, info, creator, resource_pool_id, controller_id):
        """"Получение информации о конкретном пуле ресурсов на контроллере."""
        controller = await cls.fetch_by_id(controller_id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        veil_response = await controller.veil_client.resource_pool(resource_pool_id=str(resource_pool_id)).info()
        for data in veil_response.response:
            resource_pool = data.public_attrs
            resource_pool['controller'] = {'id': controller.id,
                                           'verbose_name': controller.verbose_name,
                                           'address': controller.address}
        return ResourcePoolType(**resource_pool)

    @classmethod
    @administrator_required
    async def resolve_resource_pools(cls, root, info, creator, limit, offset, ordering: str = None):
        """Все пулы ресурсов на подключенных ECP VeiL."""
        controllers = await cls.fetch_all()
        veil_resource_pools_list = list()
        resource_pools_list = list()
        for controller in controllers:
            paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
            # Прерываем выполнение при отсутствии клиента
            if not controller.veil_client:
                continue
            veil_response = await controller.veil_client.resource_pool().list(paginator=paginator)
            for data in veil_response.response:
                resource_pool = data.public_attrs
                # Добавляем id, так как в response он не присутствует в чистом виде
                resource_pool['id'] = resource_pool['api_object_id']
                # Добавляем параметры контроллера на VDI
                resource_pool['controller'] = {'id': controller.id,
                                               'verbose_name': controller.verbose_name,
                                               'address': controller.address}
                resource_pools_list.append(resource_pool)

        if not ordering:
            resource_pools_list.sort(key=lambda data: data['verbose_name'])

        if ordering == 'controller':
            resource_pools_list.sort(key=lambda data: data['controller']['verbose_name'])
        elif ordering == '-controller':
            resource_pools_list.sort(key=lambda data: data['controller']['verbose_name'], reverse=True)

        for data in resource_pools_list:
            veil_resource_pools_list.append(ResourcePoolType(**data))

        return veil_resource_pools_list

    # Ноды
    @classmethod
    @administrator_required
    async def resolve_node(cls, root, info, creator, node_id, controller_id):
        """"Получение информации о конкретной ноде на контроллере."""
        controller = await cls.fetch_by_id(controller_id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        node_info = await controller.veil_client.node(node_id=str(node_id)).info()
        resource_data = node_info.value
        resource_data['controller'] = {'id': controller.id, 'verbose_name': controller.verbose_name}
        resource_data['cpu_count'] = resource_data['cpu_topology']['cpu_count']
        return ResourceNodeType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_nodes(cls, root, info, creator, limit, offset, ordering: str = None):
        """Все ноды (серверы) на подключенных ECP VeiL."""
        controllers = await cls.fetch_all()
        veil_nodes_list = list()
        nodes_list = list()
        for controller in controllers:
            paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
            # Прерываем выполнение при отсутствии клиента
            if not controller.veil_client:
                continue
            veil_response = await controller.veil_client.node().list(paginator=paginator)
            for node in veil_response.paginator_results:
                # Добавляем параметры контроллера на VDI
                node['controller'] = {'id': controller.id, 'verbose_name': controller.verbose_name}
                nodes_list.append(node)

        if not ordering:
            nodes_list.sort(key=lambda data: data['verbose_name'])

        if ordering == 'controller':
            nodes_list.sort(key=lambda data: data['controller']['verbose_name'])
        elif ordering == '-controller':
            nodes_list.sort(key=lambda data: data['controller']['verbose_name'], reverse=True)

        for resource_data in nodes_list:
            veil_nodes_list.append(ResourceNodeType(**resource_data))

        return veil_nodes_list

    # Пулы данных
    @classmethod
    @administrator_required
    async def resolve_datapool(cls, root, info, creator, datapool_id, controller_id):
        """Получение информации о конкретном пуле данных на контроллере."""
        controller = await cls.fetch_by_id(controller_id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        datapool_info = await controller.veil_client.data_pool(data_pool_id=str(datapool_id)).info()
        resource_data = datapool_info.value
        resource_data['controller'] = {'id': controller.id, 'verbose_name': controller.verbose_name}
        return ResourceDataPoolType(**resource_data)

    @classmethod
    @administrator_required
    async def resolve_datapools(cls, root, info, creator, limit, offset, ordering: str = None):
        """Все пулы данных (datapools) на подключенных ECP VeiL."""
        controllers = await cls.fetch_all()
        veil_datapools_list = list()
        datapools_list = list()
        for controller in controllers:
            paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
            # Прерываем выполнение при отсутствии клиента
            if not controller.veil_client:
                return
            veil_response = await controller.veil_client.data_pool().list(paginator=paginator)
            for datapool in veil_response.paginator_results:
                # Добавляем параметры контроллера на VDI
                datapool['controller'] = {'id': controller.id, 'verbose_name': controller.verbose_name}
                datapools_list.append(datapool)

        if not ordering:
            datapools_list.sort(key=lambda data: data['verbose_name'])

        if ordering == 'controller':
            datapools_list.sort(key=lambda data: data['controller']['verbose_name'])
        elif ordering == '-controller':
            datapools_list.sort(key=lambda data: data['controller']['verbose_name'], reverse=True)

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
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        veil_domain = controller.veil_client.domain(domain_id=str(domain_id))
        vm_info = await veil_domain.info()
        if vm_info.success:
            resource_data = vm_info.value
            response = await veil_domain.tags_list()
            resource_data['domain_tags'] = list()
            for tag in response.response:
                resource_data['domain_tags'].append(
                    {
                        'colour': tag.colour,
                        'verbose_name': tag.verbose_name,
                        'slug': tag.slug
                    })
            resource_data['controller'] = {'id': controller.id, 'verbose_name': controller.verbose_name}
            resource_data['cpu_count'] = veil_domain.cpu_count
            resource_data['parent_name'] = veil_domain.parent_name
            if veil_domain.guest_agent:
                resource_data['guest_agent'] = veil_domain.guest_agent.qemu_state
            if veil_domain.powered:
                resource_data['hostname'] = veil_domain.hostname
                resource_data['address'] = veil_domain.guest_agent.ipv4
            return ResourceVmType(**resource_data)
        else:
            raise SilentError(_('VM is unreachable on ECP Veil.'))

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
        """Все ВМ + шаблоны на подключенных ECP VeiL."""
        controllers = await cls.fetch_all()
        domain_list = list()
        domains = list()
        for controller in controllers:
            paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
            # Прерываем выполнение при отсутствии клиента
            if not controller.veil_client:
                continue

            veil_response = await controller.veil_client.domain(template=template).list(paginator=paginator)
            vms_list = veil_response.paginator_results

            for resource_data in vms_list:
                # Добавляем параметры контроллера и принадлежность к пулу на VDI
                resource_data['controller'] = {'id': controller.id, 'verbose_name': controller.verbose_name}
                vm = await Vm.get(resource_data['id'])
                if vm:
                    pool = await Pool.get(vm.pool_id)
                    resource_data['pool_name'] = pool.verbose_name
                else:
                    resource_data['pool_name'] = '--'
                domains.append(resource_data)

        if not ordering:
            domains.sort(key=lambda data: data['verbose_name'])

        if ordering == 'pool_name':
            domains.sort(key=lambda data: data['pool_name'])
        elif ordering == '-pool_name':
            domains.sort(key=lambda data: data['pool_name'], reverse=True)
        if ordering == 'controller':
            domains.sort(key=lambda data: data['controller']['verbose_name'])
        elif ordering == '-controller':
            domains.sort(key=lambda data: data['controller']['verbose_name'], reverse=True)

        for resource_data in domains:
            domain_list.append(ResourceVmType(**resource_data))
        return domain_list

    @classmethod
    @administrator_required
    async def resolve_vms(cls, root, info, creator, limit, offset, ordering: str = None):
        """Все сиртуальные машины на подключенных ECP VeiL."""
        # Для каждого контроллера получаем список всех ВМ за вычетом шаблонов.
        vm_type_list = await cls.domain_list(template=0, limit=limit, offset=offset, ordering=ordering)

        return vm_type_list

    @classmethod
    @administrator_required
    async def resolve_templates(cls, root, info, creator, limit, offset, ordering: str = None):
        """Все шаблоны на подключенных ECP VeiL."""
        # Для каждого контроллера получаем список всех ВМ за вычетом шаблонов.
        template_type_list = await cls.domain_list(template=1, limit=limit, offset=offset, ordering=ordering)

        return template_type_list


resources_schema = graphene.Schema(query=ResourcesQuery, auto_camelcase=False)
