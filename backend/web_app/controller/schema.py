# -*- coding: utf-8 -*-
from asyncio import TimeoutError
import re
import graphene

from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SimpleError, ValidationError
from common.veil.veil_validators import MutationValidation
from common.veil.veil_gino import StatusGraphene, Status
from common.veil.veil_graphene import VeilResourceType, VeilShortEntityType, VmState
from common.models.controller import Controller
from common.models.vm import Vm
from common.models.pool import Pool
from common.languages import lang_init
from veil_api_client import VeilRestPaginator

_ = lang_init()


class ControllerValidator(MutationValidation):
    """Валидатор входных данных для сущности Controller."""

    @staticmethod
    async def validate_verbose_name(obj_dict, value):
        """Валидатор verbose_name для контроллера."""
        # Проверяем длину значения (работает только если у валидатора value is not None)
        if not value:
            raise SimpleError(_('name can`t be empty.'))

        # Проверяем наличие записей в БД
        # TODO: универсальный метод в родительском валидаторе для сокращения дублирования
        verbose_name_is_busy = await Controller.select('id').where(Controller.verbose_name == value).gino.scalar()
        if verbose_name_is_busy:
            raise ValidationError(_('name `{}` is busy.').format(value))
        return value

    @staticmethod
    async def validate_address(obj_dict, value):
        """Валидатор адреса контроллера."""
        # Проверяем длину значения (работает только если у валидатора value is not None)
        if not value:
            raise SimpleError(_('address can`t be empty.'))

        # Проверяем наличие записей в БД
        # TODO: универсальный метод в родительском валидаторе для сокращения дублирования
        address_is_busy = await Controller.select('id').where(Controller.address == value).gino.scalar()
        if address_is_busy:
            raise ValidationError(_('address `{}` is busy.').format(value))
        return value

    @staticmethod
    async def validate_token(obj_dict, value):
        """Валидатор токена интеграции контроллера."""
        if not value:
            raise ValidationError(_('token can`t be empty.'))
        return value


class ControllerFetcher:

    @staticmethod
    async def fetch_by_id(id_):
        """Возваращает инстанс объекта, если он есть."""
        # TODO: универсальный метод в родительском валидаторе для сокращения дублированияа
        controller = await Controller.get(id_)
        if not controller:
            raise SimpleError(_('No such controller.'))
        return controller

    @staticmethod
    async def fetch_all(status=Status.ACTIVE):
        """Возвращает все записи контроллеров в определенном статусе."""
        return await Controller.query.where(Controller.status == status).gino.all()


class ControllerPoolType(graphene.ObjectType):
    """Сокращенное описание Pool."""

    id = graphene.UUID()
    verbose_name = graphene.String()
    status = StatusGraphene()
    vms_amount = graphene.Int()
    users_amount = graphene.Int()
    pool_type = graphene.String()
    keep_vms_on = graphene.Boolean()

    async def resolve_vms_amount(self, info):
        # В self лежит объект модели Pool
        return await self.get_vm_amount()

    async def resolve_users_amount(self, info):
        # В self лежит объект модели Pool
        assigned_users = await self.assigned_users
        return len(assigned_users)


class ControllerClusterType(VeilResourceType):
    """Сокращенное описание VeiL Cluster.

    Вынесен в отдельный тип для явного сокращения возможных полей.
    """

    id = graphene.UUID()
    verbose_name = graphene.String()
    description = graphene.String()
    nodes_count = graphene.Int()
    status = StatusGraphene()
    cpu_count = graphene.Int()
    memory_count = graphene.Int()
    tags = graphene.List(graphene.String)


class ControllerResourcePoolType(VeilResourceType):
    """Сокращенное описание VeiL Resource Pool.

    Вынесен в отдельный тип для явного сокращения возможных полей.
    """
    id = graphene.UUID()
    verbose_name = graphene.String()
    description = graphene.String()
    domains_count = graphene.Int()
    memory_limit = graphene.Int()
    cpu_limit = graphene.Int()


class ControllerNodeType(VeilResourceType):
    """Сокращенное описание VeiL Node.

    Вынесен в отдельный тип для явного сокращения возможных полей.
    """

    id = graphene.UUID()
    verbose_name = graphene.String()
    status = StatusGraphene()
    cpu_count = graphene.String()
    memory_count = graphene.String()
    management_ip = graphene.String()

    # Маловероятно что это нужно
    # cluster = graphene.JSONString()
    # Это вообще непонятно зачем
    # resources_usage = graphene.Field(ResourcesUsageType)
    # datacenter = graphene.Field(DatacenterType)
    # veil_info = graphene.String()
    # veil_info_json = graphene.String()


class ControllerDataPoolType(VeilResourceType):
    """Сокращенное описание VeiL DataPool."""

    id = graphene.UUID()
    verbose_name = graphene.String()
    used_space = graphene.Int()
    free_space = graphene.Int()
    size = graphene.Int()
    status = StatusGraphene()
    type = graphene.String()
    vdisk_count = graphene.Int()
    tags = graphene.List(graphene.String)
    hints = graphene.Int()
    file_count = graphene.Int()
    iso_count = graphene.Int()


class ControllerVmType(VeilResourceType):
    """Сокращенное описание Veil Domain."""

    id = graphene.UUID()
    verbose_name = graphene.String()
    template = graphene.Field(VeilShortEntityType)
    resource_pool = graphene.Field(VeilShortEntityType)
    status = StatusGraphene()
    user_power_state = VmState()
    # название пула, в котором ВМ из локальной БД
    pool_name = graphene.String()


class ControllerType(graphene.ObjectType, ControllerFetcher):
    """Описание Controller."""

    id = graphene.UUID()
    verbose_name = graphene.String()
    address = graphene.String()
    description = graphene.String()
    status = StatusGraphene()
    version = graphene.String()
    token = graphene.String()
    # Новые поля
    pools = graphene.List(ControllerPoolType)
    clusters = graphene.List(ControllerClusterType, ordering=graphene.String(), limit=graphene.Int(default_value=100),
                             offset=graphene.Int(default_value=0))
    resource_pools = graphene.List(ControllerResourcePoolType, cluster_id=graphene.UUID(), ordering=graphene.String(),
                                   limit=graphene.Int(default_value=100),
                                   offset=graphene.Int(default_value=0))
    nodes = graphene.List(ControllerNodeType, cluster_id=graphene.UUID(), resource_pool_id=graphene.UUID(),
                          ordering=graphene.String(), limit=graphene.Int(default_value=100),
                          offset=graphene.Int(default_value=0))
    data_pools = graphene.List(ControllerDataPoolType, cluster_id=graphene.UUID(), node_id=graphene.UUID(),
                               resource_pool_id=graphene.UUID(), ordering=graphene.String(),
                               limit=graphene.Int(default_value=100), offset=graphene.Int(default_value=0))
    templates = graphene.List(ControllerVmType, cluster_id=graphene.UUID(),
                              resource_pool_id=graphene.UUID(), node_id=graphene.UUID(),
                              ordering=graphene.String(),
                              limit=graphene.Int(default_value=100), offset=graphene.Int(default_value=0))
    vms = graphene.List(ControllerVmType, cluster_id=graphene.UUID(),
                        resource_pool_id=graphene.UUID(), node_id=graphene.UUID(),
                        exclude_existed=graphene.Boolean(), ordering=graphene.String(),
                        limit=graphene.Int(default_value=100), offset=graphene.Int(default_value=0))

    async def resolve_pools(self, info):
        """В self прилетает инстанс подели контроллера."""
        controller = await Controller.get(self.id)
        return await controller.pools

    async def resolve_clusters(self, info, limit, offset, ordering: str = None):
        """В self прилетает инстанс модели контроллера."""
        controller = await Controller.get(self.id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
        veil_response = await controller.veil_client.cluster().list(paginator=paginator)
        return [ControllerClusterType(**resource_data) for resource_data in veil_response.paginator_results]

    async def resolve_resource_pools(self, info, limit, offset, cluster_id=None, ordering: str = None):
        """В self прилетает инстанс модели контроллера."""
        controller = await Controller.get(self.id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
        veil_response = await controller.veil_client.resource_pool(cluster_id=cluster_id).list(paginator=paginator)
        return [ControllerResourcePoolType(**data) for data in veil_response.paginator_results]

    async def resolve_nodes(self, info, limit, offset, cluster_id=None, resource_pool_id=None, ordering: str = None):
        """В self прилетает инстанс модели контроллера."""
        controller = await Controller.get(self.id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
        veil_response = await controller.veil_client.node(cluster_id=cluster_id,
                                                          resource_pool_id=resource_pool_id).list(paginator=paginator)
        return [ControllerNodeType(**resource_data) for resource_data in veil_response.paginator_results]

    async def resolve_data_pools(self, info, limit, offset, cluster_id=None, node_id=None, resource_pool_id=None,
                                 ordering: str = None):
        """Сокращенная информация о контроллере."""
        # TODO: на фронте делать неактивными элементы в плохом статусе?
        controller = await Controller.get(self.id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
        veil_response = await controller.veil_client.data_pool(cluster_id=cluster_id,
                                                               resource_pool_id=resource_pool_id,
                                                               node_id=node_id).list(paginator=paginator)
        return [ControllerDataPoolType(**resource_data) for resource_data in veil_response.paginator_results]

    async def resolve_templates(self, info, limit, offset, cluster_id=None, resource_pool_id=None,
                                node_id=None, ordering: str = None):
        """В self прилетает инстанс модели контроллера."""
        # TODO: на фронте делать неактивными элементы в плохом статусе?
        controller = await Controller.get(self.id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
        veil_response = await controller.veil_client.domain(template=1,
                                                            cluster_id=cluster_id,
                                                            resource_pool=resource_pool_id,
                                                            node_id=node_id).list(paginator=paginator)
        return [ControllerVmType(**data) for data in veil_response.paginator_results]

    async def resolve_vms(self, info, limit, offset, cluster_id=None, resource_pool_id=None, node_id=None,
                          exclude_existed=True, ordering: str = None):
        """В self прилетает инстанс модели контроллера."""
        # TODO: на фронте делать неактивными элементы в плохом статусе?
        controller = await Controller.get(self.id)
        paginator = VeilRestPaginator(ordering=ordering, limit=limit, offset=offset)
        vms = await Vm.query.gino.all()
        # Прерываем выполнение при отсутствии клиента
        if controller.veil_client:
            veil_response = await controller.veil_client.domain(template=0,
                                                                cluster_id=cluster_id,
                                                                resource_pool=resource_pool_id,
                                                                node_id=node_id).list(paginator=paginator)
            resolves = veil_response.paginator_results
        else:
            resolves = dict()
        vms_list = []
        if exclude_existed:
            for vm in vms:
                for index, data in enumerate(resolves):
                    if str(data['id']) == str(vm.id):
                        del resolves[index]
        for resource in resolves:
            resource['template'] = resource['parent']
            vm = await Vm.get(resource['id'])
            if vm:
                pool = await Pool.get(vm.pool_id)
                resource['pool_name'] = pool.verbose_name
            else:
                resource['pool_name'] = '--'

        if ordering == 'pool_name':
            resolves.sort(key=lambda data: data['pool_name'])
        elif ordering == '-pool_name':
            resolves.sort(key=lambda data: data['pool_name'], reverse=True)

        for resource in resolves:
            vms_list.append(ControllerVmType(**resource))
        return vms_list

    @staticmethod
    def obj_to_type(controller_obj: Controller) -> dict:
        if controller_obj and isinstance(controller_obj, Controller):
            controller_dict = {'id': controller_obj.id,
                               'verbose_name': controller_obj.verbose_name,
                               'address': controller_obj.address,
                               'description': controller_obj.description,
                               'status': controller_obj.status,
                               'version': controller_obj.version,
                               'token': '*' * 12,
                               }
            return ControllerType(**controller_dict)


class AddControllerMutation(graphene.Mutation, ControllerValidator):
    """Добавление контроллера."""

    class Arguments:
        verbose_name = graphene.String(required=True)
        address = graphene.String(required=True)
        token = graphene.String(required=True)
        description = graphene.String()

    controller = graphene.Field(lambda: ControllerType)
    __TOKEN_PREFIX = re.compile('jwt ', re.I)

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, **kwargs):
        # Валидируем аргументы
        await cls.validate(**kwargs)
        if not cls.__TOKEN_PREFIX.match(kwargs['token']):
            kwargs['token'] = ' '.join(['jwt', kwargs['token']])
        # Формат токена дополнительно валидируется в veil api client
        try:
            controller = await Controller.soft_create(**kwargs)
        except TimeoutError:
            raise SimpleError(_('Connection to ECP has been failed.'))
        else:
            return AddControllerMutation(controller=controller)


class UpdateControllerMutation(graphene.Mutation, ControllerValidator, ControllerFetcher):
    """Редактирование сущности контроллера."""

    class Arguments:
        id_ = graphene.UUID(required=True)
        verbose_name = graphene.String()
        address = graphene.String()
        description = graphene.String()
        token = graphene.String()

    controller = graphene.Field(lambda: ControllerType)
    __TOKEN_PREFIX = re.compile('jwt ', re.I)

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, id_, creator, **kwargs):
        # Проверяем наличие записи
        controller = await cls.fetch_by_id(id_)
        # Валидируем переданные аргументы
        await cls.validate(**kwargs)
        if kwargs.get('token') and not cls.__TOKEN_PREFIX.match(kwargs['token']):
            kwargs['token'] = ' '.join(['jwt', kwargs['token']])
        # Формат токена дополнительно валидируется в veil api client
        try:
            updated_controller = await controller.soft_update(creator=creator, **kwargs)
        except TimeoutError:
            raise SimpleError(_('Connection to ECP has been failed.'))
        else:
            return UpdateControllerMutation(controller=updated_controller)


class RemoveControllerMutation(graphene.Mutation, ControllerFetcher):
    """Удаление сущности контроллера."""

    class Arguments:
        id_ = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, id_, creator):
        controller = await cls.fetch_by_id(id_)
        status = await controller.full_delete(creator=creator)
        return RemoveControllerMutation(ok=status)


class TestControllerMutation(graphene.Mutation, ControllerFetcher):
    """Проверка соединения с контроллером."""

    class Arguments:
        id_ = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, id_, creator):
        controller = await cls.fetch_by_id(id_)
        ok = await controller.check_controller()

        return TestControllerMutation(ok=ok)


class ServiceControllerMutation(graphene.Mutation, ControllerFetcher):
    class Arguments:
        id_ = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, id_, creator):
        controller = await cls.fetch_by_id(id_)
        ok = await controller.service(status=Status.SERVICE, creator=creator)

        return ServiceControllerMutation(ok=ok)


class ActivateControllerMutation(graphene.Mutation, ControllerFetcher):
    class Arguments:
        id_ = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, id_, creator):
        controller = await cls.fetch_by_id(id_)
        ok = await controller.enable(creator=creator)

        return ActivateControllerMutation(ok=ok)


class ControllerQuery(graphene.ObjectType, ControllerFetcher):
    controllers = graphene.List(ControllerType, limit=graphene.Int(default_value=100),
                                offset=graphene.Int(default_value=0), ordering=graphene.String(),
                                status=StatusGraphene())
    controller = graphene.Field(ControllerType, id_=graphene.UUID())

    @staticmethod
    def build_filters(status):
        filters = []
        if status is not None:
            filters.append((Controller.status == status))

        return filters

    @administrator_required
    async def resolve_controllers(self, info, limit, offset, status=None, ordering=None, **kwargs):
        filters = ControllerQuery.build_filters(status)
        controllers = await Controller.get_objects(limit, offset, filters=filters, ordering=ordering,
                                                   include_inactive=True)
        return controllers

    @classmethod
    @administrator_required
    async def resolve_controller(cls, root, info, id_, creator):
        controller = await cls.fetch_by_id(id_)
        return ControllerType.obj_to_type(controller)


class ControllerMutations(graphene.ObjectType):
    addController = AddControllerMutation.Field()
    updateController = UpdateControllerMutation.Field()
    removeController = RemoveControllerMutation.Field()
    testController = TestControllerMutation.Field()
    serviceController = ServiceControllerMutation.Field()
    activateController = ActivateControllerMutation.Field()


controller_schema = graphene.Schema(query=ControllerQuery,
                                    mutation=ControllerMutations,
                                    auto_camelcase=False)
