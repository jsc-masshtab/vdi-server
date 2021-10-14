# -*- coding: utf-8 -*-
import asyncio
import re
from uuid import UUID

from asyncpg.exceptions import UniqueViolationError

import graphene

from common.database import db
from common.graphene_utils import ShortString
from common.languages import _local_
from common.log.journal import system_logger
from common.models.auth import Entity, User
from common.models.controller import Controller
from common.models.pool import AutomatedPool, Pool, RdsPool, StaticPool
from common.models.task import PoolTaskType, Task, TaskStatus
from common.models.vm import Vm
from common.settings import (
    DOMAIN_CREATION_MAX_STEP,
    POOL_MAX_SIZE,
    POOL_MIN_SIZE
)
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SilentError, SimpleError, ValidationError
from common.veil.veil_gino import (
    EntityType,
    Role,
    RoleTypeGraphene,
    Status,
    StatusGraphene,
    VeilModel
)
from common.veil.veil_graphene import (
    VeilResourceType,
    VeilShortEntityType,
    VeilTagsType,
    VmState,
)
from common.veil.veil_redis import (
    execute_delete_pool_task,
    request_to_execute_pool_task,
    wait_for_task_result,
)
from common.veil.veil_validators import MutationValidation

from web_app.auth.user_schema import UserType
from web_app.controller.resource_schema import ResourceDataPoolType
from web_app.controller.schema import ControllerType
from web_app.journal.schema import EntityType as TypeEntity, EventType

ConnectionTypesGraphene = graphene.Enum.from_enum(Pool.PoolConnectionTypes)

# TODO: отсутствует валидация входящих ресурсов вроде node_uid, cluster_uid и т.п. Ранее шла речь,
#  о том, что мы будем кешированно хранить какие-то ресурсы полученные от ECP Veil. Возможно стоит
#  обращаться к этому хранилищу для проверки корректности присланных ресурсов. Аналогичный принцип
#  стоит применить и к статическим пулам (вместо похода на вейл для проверки присланных параметров).


class ControllerFetcher:

    @staticmethod
    async def fetch_by_id(id_):
        """Возваращает инстанс объекта, если он есть."""
        controller = await Controller.get(id_)
        if not controller:
            raise SimpleError(_local_("No such controller."))
        return controller

    @staticmethod
    async def fetch_all(status=Status.ACTIVE):
        """Возвращает все записи контроллеров в определенном статусе."""
        return await Controller.query.where(Controller.status == status).gino.all()


class VmBackupType(VeilResourceType):
    file_id = graphene.Field(ShortString)
    filename = graphene.Field(ShortString)
    size = graphene.Field(ShortString)
    assignment_type = graphene.Field(ShortString)
    datapool = graphene.Field(ResourceDataPoolType)
    node = graphene.Field(VeilShortEntityType)
    vm_id = graphene.Field(ShortString)
    status = StatusGraphene()


class VmConnectionType(VeilResourceType):
    password = graphene.Field(ShortString)
    host = graphene.Field(ShortString)
    token = graphene.Field(ShortString)
    connection_url = graphene.Field(ShortString)
    connection_type = graphene.Field(ShortString)


class VmType(VeilResourceType):
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
    user_power_state = VmState(description="Питание")
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
    user = graphene.Field(UserType)
    assigned_users = graphene.List(
        UserType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )
    assigned_users_count = graphene.Int()
    # controller = graphene.Field(ControllerType)
    # qemu_state = graphene.Boolean(description='Состояние гостевого агента')
    qemu_state = VmState(description="Состояние гостевого агента")
    node = graphene.Field(VeilShortEntityType)
    backups = graphene.List(VmBackupType)

    # Список событий для отдельной ВМ и отдельное событие внутри пула
    count = graphene.Int()
    events = graphene.List(
        EventType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )
    event = graphene.Field(EventType, event_id=graphene.UUID())
    spice_connection = graphene.Field(VmConnectionType)
    vnc_connection = graphene.Field(VmConnectionType)

    async def resolve_user(self, _info):
        vm = await Vm.get(self.id)
        username = await vm.username if vm else None
        return UserType(username=username)

    async def resolve_assigned_users(self, _info, limit, offset):
        """Получить список пользователей ВМ."""
        vm = await Vm.get(self.id)
        if vm:
            users_query = await vm.get_users_query()
            users = await users_query.limit(limit).offset(offset).gino.all()
            objects = [UserType.instance_to_type(user) for user in users]
            return objects
        return list()

    async def resolve_assigned_users_count(self, _info):
        vm = await Vm.get(self.id)
        count = await vm.get_users_count()
        return count

    async def resolve_count(self, _info, **kwargs):
        vm_obj = await Vm.get(self.id)
        events_count = await vm_obj.events_count()
        return events_count

    async def resolve_events(self, _info, limit, offset):
        vm_obj = await Vm.get(self.id)
        events = await vm_obj.events(limit=limit, offset=offset)
        event_type_list = [
            EventType(
                read_by=[UserType(**user.__values__) for user in event.read_by],
                entity=[TypeEntity(**entity.__values__) for entity in event.entity],
                **event.__values__
            )
            for event in events
        ]
        return event_type_list

    async def resolve_event(self, _info, event_id):
        event = await Vm.event(event_id)
        event_type = EventType(
            read_by=[UserType(**user.__values__) for user in event.read_by],
            entity=[entity for entity in event.entity],
            **event.__values__
        )
        return event_type

    async def resolve_backups(self, _info, **kwargs):
        vm_obj = await Vm.get(self.id)
        domain_entity = await vm_obj.vm_client
        if domain_entity:
            await domain_entity.info()
            # Список бэкапов ВМ
            response = await domain_entity.backup_list()
            veil_backups_list = list()
            backups_list = list()
            for data in response.response:
                backup = data.public_attrs
                backup["file_id"] = backup["api_object_id"]
                backup["node"] = self.node
                backup["vm_id"] = self.id
                backups_list.append(backup)

            for data in backups_list:
                veil_backups_list.append(VmBackupType(**data))

            return veil_backups_list

    async def resolve_spice_connection(self, _info, **kwargs):
        vm_obj = await Vm.get(self.id)
        domain_entity = await vm_obj.vm_client
        await domain_entity.info()
        if domain_entity.powered:
            spice = await domain_entity.spice_conn()
            if spice and spice.valid:
                return VmConnectionType(password=spice.password,
                                        host=spice.host,
                                        token=spice.token,
                                        connection_url=spice.connection_url,
                                        connection_type=spice.connection_type)
            raise SimpleError(_local_("Missing connection spice data."))

    async def resolve_vnc_connection(self, _info, **kwargs):
        vm_obj = await Vm.get(self.id)
        domain_entity = await vm_obj.vm_client
        await domain_entity.info()
        if domain_entity.powered:
            vnc = await domain_entity.vnc_conn()
            if vnc and vnc.valid:
                return VmConnectionType(password=vnc.password,
                                        host=vnc.host,
                                        token=vnc.token,
                                        connection_url=vnc.connection_url,
                                        connection_type=vnc.connection_type)
            raise SimpleError(_local_("Missing connection vnc data."))


class VmInput(graphene.InputObjectType):
    """Инпут для ввода ВМ."""

    id = graphene.UUID()
    verbose_name = ShortString()


class PoolValidator(MutationValidation):
    """Валидатор для сущности Pool."""

    @staticmethod
    async def validate_pool_id(obj_dict, value):
        if not value:
            return
        pool = await Pool.get(value)
        if pool:
            return value
        raise ValidationError(_local_("No such pool."))

    @staticmethod
    async def validate_verbose_name(obj_dict, value):
        if not value:
            return
        name_re = re.compile("^[а-яА-ЯёЁa-zA-Z0-9\\-]*$")
        template_name = re.match(name_re, value)
        if template_name:
            return value
        raise ValidationError(
            _local_("Pool name must contain only characters, digits and -.")
        )

    @staticmethod
    async def validate_vm_name_template(obj_dict, value):
        if not value:
            return

        min_len = 2
        max_len = 63
        name_re = re.compile("^[a-zA-Z]+[a-zA-Z0-9-]{2,63}$")
        template_name = re.match(name_re, value)
        if template_name:
            return value
        raise ValidationError(
            _local_(
                "Template name of VM must contain only characters, digits, -. "
                "Template name length must be in [{} {}] interval."
            ).format(min_len, max_len)
        )

    @staticmethod
    async def validate_initial_size(obj_dict, value):
        if value is None:
            return
        if value < POOL_MIN_SIZE or value > POOL_MAX_SIZE:
            raise ValidationError(
                _local_("Initial number of VM must be in {}-{} interval.").format(
                    POOL_MIN_SIZE, POOL_MAX_SIZE
                )
            )
        return value

    @staticmethod
    async def validate_reserve_size(obj_dict, value):
        if value is None:
            return

        pool_id = obj_dict.get("pool_id")
        if pool_id:
            pool_obj = await Pool.get_pool(pool_id)
            total_size = (
                obj_dict["total_size"]
                if obj_dict.get("total_size")
                else pool_obj.total_size
            )
        else:
            total_size = obj_dict["total_size"]

        if value > total_size:
            raise ValidationError(
                _local_("Reserve size of VMs can not be more than maximal number of Vms.")
            )

        if value < POOL_MIN_SIZE or value > POOL_MAX_SIZE:
            raise ValidationError(
                _local_("Reserve size of VM must be in {}-{} interval.").format(
                    POOL_MIN_SIZE, POOL_MAX_SIZE
                )
            )
        return value

    @staticmethod
    async def validate_total_size(obj_dict, value):
        if value is None:
            return

        pool_id = obj_dict.get("pool_id")
        if pool_id:
            pool_obj = await Pool.get_pool(pool_id)
            initial_size = (
                obj_dict["initial_size"]
                if obj_dict.get("initial_size")
                else pool_obj.initial_size
            )

            pool_model = await Pool.get(pool_id)
            vm_amount_in_pool = await pool_model.get_vm_amount()
        else:
            initial_size = obj_dict["initial_size"]
            vm_amount_in_pool = None

        if value < initial_size:
            raise ValidationError(
                _local_(
                    "Maximal number of created VM can not be less than initial number of VM."
                )
            )
        if value < POOL_MIN_SIZE or value > POOL_MAX_SIZE:
            raise ValidationError(
                _local_(
                    "Maximal number of created VM must be in [{} {}] interval.").format(
                    POOL_MIN_SIZE, POOL_MAX_SIZE
                )
            )
        if vm_amount_in_pool and value < vm_amount_in_pool:
            raise ValidationError(
                _local_(
                    "Maximal number of created VMs can not be less than current amount of Vms."
                )
            )
        return value

    @staticmethod
    async def validate_increase_step(obj_dict, value):
        if value is None:
            return

        total_size = obj_dict["total_size"] if obj_dict.get("total_size") else None
        if total_size is None:
            pool_id = obj_dict.get("pool_id")
            automated_pool = await AutomatedPool.get(pool_id)
            if automated_pool:
                total_size = automated_pool.total_size
        if value < 1 or value > total_size:
            raise ValidationError(
                _local_(
                    "Increase step must be positive and less or equal to total_size.")
            )
        if value > DOMAIN_CREATION_MAX_STEP:
            raise ValidationError(
                _local_("Increase step must be less than {}.").format(
                    DOMAIN_CREATION_MAX_STEP)
            )
        return value

    @staticmethod
    async def validate_connection_types(obj_dict, value):
        if not value:
            raise ValidationError(_local_("Connection type cannot be empty."))


class PoolGroupType(graphene.ObjectType):
    """Намеренное дублирование UserGroupType и GroupType +с сокращением доступных полей.

    Нет понимания в целесообразности абстрактного класса для обоих типов.
    """

    id = graphene.UUID(required=True)
    verbose_name = ShortString()
    description = ShortString()

    @staticmethod
    def instance_to_type(model_instance):
        return PoolGroupType(
            id=model_instance.id,
            verbose_name=model_instance.verbose_name,
            description=model_instance.description,
        )


class PoolType(graphene.ObjectType):

    # Pool fields
    master_id = graphene.UUID()
    pool_id = graphene.UUID()
    verbose_name = ShortString()
    status = StatusGraphene()
    pool_type = ShortString()
    resource_pool_id = graphene.UUID()
    controller = graphene.Field(ControllerType)
    vm_amount = graphene.Int()

    # StaticPool fields
    static_pool_id = graphene.UUID()

    # AutomatedPool fields
    automated_pool_id = graphene.UUID()
    datapool_id = graphene.UUID()
    template_id = graphene.UUID()
    increase_step = graphene.Int()
    max_amount_of_create_attempts = graphene.Int()
    initial_size = graphene.Int()
    reserve_size = graphene.Int()
    total_size = graphene.Int()
    waiting_time = graphene.Int()
    vm_name_template = ShortString()
    os_type = ShortString()
    ad_ou = ShortString()

    users_count = graphene.Int(entitled=graphene.Boolean())
    users = graphene.List(UserType,
                          limit=graphene.Int(default_value=500),
                          offset=graphene.Int(default_value=0),
                          entitled=graphene.Boolean(),
                          ordering=ShortString())
    assigned_roles = graphene.List(RoleTypeGraphene)
    possible_roles = graphene.List(RoleTypeGraphene)
    assigned_groups = graphene.List(
        PoolGroupType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        ordering=ShortString()
    )
    possible_groups = graphene.List(PoolGroupType)

    keep_vms_on = graphene.Boolean()
    create_thin_clones = graphene.Boolean()
    enable_vms_remote_access = graphene.Boolean()
    start_vms = graphene.Boolean()
    set_vms_hostnames = graphene.Boolean()
    include_vms_in_ad = graphene.Boolean()
    assigned_connection_types = graphene.List(ConnectionTypesGraphene)
    possible_connection_types = graphene.List(ConnectionTypesGraphene)

    # Затрагивает запрос ресурсов на VeiL ECP.
    template = graphene.Field(VeilShortEntityType)
    resource_pool = graphene.Field(VeilShortEntityType)
    datapool = graphene.Field(VeilShortEntityType)
    vms = graphene.List(VmType,
                        limit=graphene.Int(default_value=500),
                        offset=graphene.Int(default_value=0),
                        ordering=ShortString())
    vm = graphene.Field(VmType, vm_id=graphene.UUID(), controller_id=graphene.UUID())

    async def resolve_controller(self, info):
        controller_obj = await Controller.get(self.controller)
        return ControllerType(**controller_obj.__values__)

    async def resolve_assigned_roles(self, info):
        pool = await Pool.get(self.pool_id)
        roles = await pool.roles
        for index, role in enumerate(roles):
            if not all(role):
                del roles[index]

        return [role_type.role for role_type in roles]

    async def resolve_possible_roles(self, info):
        assigned_roles = await self.resolve_assigned_roles(info=info)
        all_roles = [role_type.value for role_type in Role]
        possible_roles = [role for role in all_roles if role not in assigned_roles]
        return possible_roles

    async def resolve_assigned_groups(self, info, limit, offset, ordering=None):
        pool = await Pool.get(self.pool_id)
        return await pool.assigned_groups_paginator(limit=limit, offset=offset,
                                                    ordering=ordering)

    async def resolve_possible_groups(self, _info):
        pool = await Pool.get(self.pool_id)
        return await pool.possible_groups

    async def resolve_users_count(self, _info, entitled=True):
        pool = await Pool.get(self.pool_id)
        if entitled:
            return await pool.assigned_users_count()
        else:
            return await pool.possible_users_count()

    async def resolve_users(self, _info, limit=500, offset=0, entitled=True, ordering=None):
        pool = await Pool.get(self.pool_id)
        if entitled:
            return await pool.assigned_users(ordering=ordering, limit=limit, offset=offset)
        return await pool.possible_users(limit=limit, offset=offset)  # ordered by name inside the method

    async def resolve_vms(self, _info, limit=500, offset=0, ordering=None):

        pool = await Pool.get(self.pool_id)
        vms_info = await pool.get_vms_info(limit=limit, offset=offset, ordering=ordering)
        return vms_info

    @classmethod
    async def domain_info(cls, domain_id, controller_id):
        controller = await Controller.get(controller_id)
        vm = await Vm.get(domain_id)
        # Прерываем выполнение при отсутствии клиента
        if not controller.veil_client:
            return
        veil_domain = controller.veil_client.domain(domain_id=str(domain_id))
        vm_info = await veil_domain.info()
        if vm_info.success:
            data = vm_info.value
            response = await veil_domain.tags_list()
            data["domain_tags"] = list()
            for tag in response.response:
                data["domain_tags"].append(
                    {
                        "colour": tag.colour,
                        "verbose_name": tag.verbose_name,
                        "slug": tag.slug,
                    }
                )
            data["controller"] = {
                "id": controller.id,
                "verbose_name": controller.verbose_name,
            }
            data["cpu_count"] = veil_domain.cpu_count_prop
            data["parent_name"] = veil_domain.parent_name
            data["status"] = vm.status
            if veil_domain.guest_agent:
                data["guest_agent"] = veil_domain.guest_agent.qemu_state
            if veil_domain.powered:
                data["hostname"] = veil_domain.hostname
                if veil_domain.guest_agent:
                    data["address"] = veil_domain.guest_agent.ipv4
            return VmType(**data)
        else:
            raise SilentError(_local_("VM is unreachable on ECP VeiL."))

    @classmethod
    @administrator_required
    async def resolve_vm(cls, root, info, creator, vm_id, controller_id):
        """Обёртка для получения информации о ВМ на ECP."""
        return await cls.domain_info(domain_id=vm_id, controller_id=controller_id)

    async def resolve_vm_amount(self, _info):
        return await (
            db.select([db.func.count(Vm.id)]).where(Vm.pool_id == self.pool_id)
        ).gino.scalar()

    async def resolve_resource_pool(self, _info):
        pool = await Pool.get(self.pool_id)
        pool_controller = await pool.controller_obj
        # Прерываем выполнение при отсутствии клиента
        if not pool_controller.veil_client:
            return
        resource_pool_info = await pool_controller.veil_client.resource_pool(
            resource_pool_id=str(pool.resource_pool_id)
        ).info()
        data = resource_pool_info.value
        return VeilShortEntityType(**data)

    async def resolve_template(self, _info):
        pool = await Pool.get(self.pool_id)
        pool_controller = await pool.controller_obj
        template_id = await pool.template_id
        if not template_id:
            return
        # Прерываем выполнение при отсутствии клиента
        if not pool_controller.veil_client:
            return
        veil_domain = pool_controller.veil_client.domain(str(template_id))
        await veil_domain.info()
        # попытка не использовать id
        veil_domain.id = veil_domain.api_object_id
        return veil_domain

    async def resolve_datapool(self, _info):
        pool = await Pool.get(self.pool_id)
        pool_controller = await pool.controller_obj
        # Прерываем выполнение при отсутствии клиента
        if not pool_controller.veil_client:
            return
        if pool.datapool_id:
            veil_datapool = pool_controller.veil_client.data_pool(str(pool.datapool_id))
            await veil_datapool.info()
            # попытка не использовать id
            veil_datapool.id = veil_datapool.api_object_id
            return veil_datapool
        return None

    async def resolve_assigned_connection_types(self, _info):
        pool = await Pool.get(self.pool_id)
        return pool.connection_types

    async def resolve_possible_connection_types(self, _info):
        pool = await Pool.get(self.pool_id)
        return await pool.possible_connection_types


def pool_obj_to_type(pool_obj: Pool) -> PoolType:
    pool_dict = {
        "pool_id": pool_obj.master_id,
        "master_id": pool_obj.master_id,
        "verbose_name": pool_obj.verbose_name,
        "pool_type": pool_obj.pool_type.name,
        "resource_pool_id": pool_obj.resource_pool_id,
        "static_pool_id": pool_obj.master_id,
        "automated_pool_id": pool_obj.master_id,
        "datapool_id": pool_obj.datapool_id,
        "template_id": pool_obj.template_id,
        "increase_step": pool_obj.increase_step,
        "max_amount_of_create_attempts": pool_obj.max_amount_of_create_attempts,
        "initial_size": pool_obj.initial_size,
        "reserve_size": pool_obj.reserve_size,
        "total_size": pool_obj.total_size,
        "waiting_time": pool_obj.waiting_time,
        "vm_name_template": pool_obj.vm_name_template,
        "os_type": pool_obj.os_type,
        "keep_vms_on": pool_obj.keep_vms_on,
        "ad_ou": pool_obj.ad_ou,
        "create_thin_clones": pool_obj.create_thin_clones,
        "enable_vms_remote_access": pool_obj.enable_vms_remote_access,
        "start_vms": pool_obj.start_vms,
        "set_vms_hostnames": pool_obj.set_vms_hostnames,
        "include_vms_in_ad": pool_obj.include_vms_in_ad,
        "controller": pool_obj.controller,
        "status": pool_obj.status,
        # 'assigned_connection_types': pool_obj.connection_types
    }
    return PoolType(**pool_dict)


class PoolQuery(graphene.ObjectType):
    pools = graphene.List(
        PoolType,
        status=StatusGraphene(),
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        ordering=ShortString(),
    )
    pool = graphene.Field(PoolType, pool_id=ShortString())

    @staticmethod
    def build_filters(status):
        filters = []
        if status is not None:
            filters.append((Pool.status == status))

        return filters

    @administrator_required
    async def resolve_pools(
        self, info, limit, offset, status=None, ordering=None, **kwargs
    ):
        filters = PoolQuery.build_filters(status)

        # Сортировка может быть по полю модели Pool, либо по Pool.EXTRA_ORDER_FIELDS
        pools = await Pool.get_pools(limit, offset, filters=filters, ordering=ordering)
        objects = [pool_obj_to_type(pool) for pool in pools]
        return objects

    @administrator_required
    async def resolve_pool(self, _info, pool_id, **kwargs):
        pool = await Pool.get_pool(pool_id)
        if not pool:
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(_local_("No such pool."), entity=entity)
        return pool_obj_to_type(pool)


# --- --- --- --- ---
# Pool mutations
class DeletePoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        pool_id = graphene.UUID()
        full = graphene.Boolean(required=False)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, info, pool_id, creator, full=True):

        # Нет запуска валидации, т.к. нужна сущность пула далее - нет смысла запускать запрос 2жды.
        # print('pool_id', pool_id)
        pool = await Pool.get(pool_id)
        if not pool:
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(_local_("No such pool."), entity=entity)

        pool_type = pool.pool_type

        # Авто пул или Гостевой пул
        if pool_type == Pool.PoolTypes.AUTOMATED or pool_type == Pool.PoolTypes.GUEST:
            await execute_delete_pool_task(
                str(pool.id), full=full, wait_for_result=False
            )
            return DeletePoolMutation(ok=True)
        else:
            is_deleted = await Pool.delete_pool(pool, creator)
            return DeletePoolMutation(ok=is_deleted)


class ClearPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, info, pool_id, creator):
        pool = await Pool.get(pool_id)
        if (pool.status != Status.ACTIVE) and (pool.status != Status.SERVICE):
            await pool.activate(pool.id)
            await system_logger.info(
                _local_("Pool {} has been restored.").format(pool.verbose_name),
                user=creator
            )
            return ClearPoolMutation(ok=True)
        elif pool.status == Status.SERVICE:
            raise SilentError(
                _local_("Pool {} is in service mode.").format(pool.verbose_name)
            )
        else:
            raise SilentError(
                _local_("Pool {} is already active.").format(pool.verbose_name))


# --- --- --- --- ---
# Static pool mutations
class CreateStaticPoolMutation(graphene.Mutation, ControllerFetcher):
    """Создание статического пула.

    Стаический пул это группа ВМ, которые уже созданы на VeiL ECP.
    на данный момент ВМ не может одновременно находиться в нескольких статических пулах
    валидатор исключен, потому что все входные параметры можно провалидировать
    только после отправки команды на ECP VeiL.
    """

    class Arguments:
        controller_id = graphene.UUID(required=True)
        resource_pool_id = graphene.UUID(required=True)
        verbose_name = ShortString(required=True)
        vms = graphene.NonNull(graphene.List(graphene.NonNull(VmInput)))
        connection_types = graphene.List(
            graphene.NonNull(ConnectionTypesGraphene),
            default_value=[Pool.PoolConnectionTypes.SPICE.value],
        )

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(
        cls,
        root,
        info,
        creator,
        controller_id,
        resource_pool_id,
        verbose_name,
        vms,
        connection_types,
    ):
        """Мутация создания Статического пула виртуальных машин.

        1. Проверка переданных vm_ids
        2. Получение дополнительной информации (resource_pool_id, controller_address
        3. Создание Pool
        4. Создание StaticPool
        5. Создание не удаляемых VM в локальной таблице VM
        6. Разрешение удаленного доступа к VM на veil
        7. Активация Pool
        """
        # Проверяем наличие записи
        controller = await cls.fetch_by_id(controller_id)

        # --- Создание записей в БД
        try:
            tag = await Pool.tag_create(
                controller=controller, verbose_name=verbose_name, creator=creator
            )

            pool = await StaticPool.soft_create(
                veil_vm_data=vms,
                verbose_name=verbose_name,
                resource_pool_id=resource_pool_id,
                controller_id=controller_id,
                connection_types=connection_types,
                tag=tag,
                creator=creator,
            )
        except UniqueViolationError as E:
            desc = str(E)
            error_msg = _local_("Failed to create static pool {}.").format(verbose_name)
            await system_logger.debug(desc)
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(error_msg, description=desc, entity=entity)

        # Запустить задачи подготовки машин
        for vm_data in vms:
            await request_to_execute_pool_task(
                vm_data.id, PoolTaskType.VM_PREPARE, full=False
            )

        return {
            "pool": PoolType(pool_id=pool.id, verbose_name=verbose_name, vms=vms),
            "ok": True,
        }


class CreateRdsPoolMutation(graphene.Mutation, PoolValidator, ControllerFetcher):
    """Создание RDS пула. Пул состоит из одной машины - Сервера RDS.

    Конкретные права определяются уже внутри RDS
    """

    class Arguments:
        controller_id = graphene.UUID(required=True)
        resource_pool_id = graphene.UUID(required=True)
        rds_vm = VmInput(required=True)
        verbose_name = ShortString(required=True)
        connection_types = graphene.List(
            graphene.NonNull(ConnectionTypesGraphene),
            default_value=[Pool.PoolConnectionTypes.RDP.value],
        )

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, creator, controller_id,
                     resource_pool_id, rds_vm, verbose_name, connection_types):

        RdsPool.validate_conn_types(connection_types)

        await cls.validate(verbose_name=verbose_name)

        # Create pool
        pool = await RdsPool.soft_create(
            controller_id=controller_id,
            rds_id=rds_vm.id,
            rds_verbose_name=rds_vm.verbose_name,
            verbose_name=verbose_name,
            resource_pool_id=resource_pool_id,
            connection_types=set(connection_types),
            creator=creator,
        )

        return {
            "pool": PoolType(pool_id=pool.id, verbose_name=verbose_name),
            "ok": True,
        }


class AddVmsToStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        # vm_ids = graphene.List(graphene.UUID, required=True)
        vms = graphene.NonNull(graphene.List(graphene.NonNull(VmInput)))

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, pool_id, vms, creator):
        pool = await Pool.get(pool_id)
        used_vm_ids = (
            await Vm.get_all_vms_ids()
        )  # get list of vms which are already in pools

        for vm_id in [vm.id for vm in vms]:
            if vm_id in used_vm_ids:
                entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
                raise SimpleError(
                    _local_("VM {} is already in one of pools.").format(vm_id),
                    entity=entity
                )

        vm_objects = list()
        # Add VMs to db
        for vm in vms:
            vm = await Vm.create(
                id=vm.id,
                template_id=None,
                pool_id=pool_id,
                created_by_vdi=False,
                verbose_name=vm.verbose_name,
            )
            vm_objects.append(vm)
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            await system_logger.info(
                _local_("VM {} has been added to the pool {}.").format(
                    vm.verbose_name, pool.verbose_name
                ),
                user=creator,
                entity=entity,
            )

            # Запустить задачи подготовки машин
            await request_to_execute_pool_task(
                vm.id, PoolTaskType.VM_PREPARE, full=False
            )

        # Разом прикрепляем теги
        if pool.tag and vm_objects:
            await pool.tag_add_entities(tag=pool.tag, vm_objects=vm_objects)
        return {"ok": True}


class UpdateStaticPoolMutation(graphene.Mutation, PoolValidator):
    """ """

    class Arguments:
        pool_id = graphene.UUID(required=True)
        verbose_name = ShortString()
        keep_vms_on = graphene.Boolean()
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene))

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, _root, _info, creator, **kwargs):
        await cls.validate(**kwargs)
        try:
            ok = await StaticPool.soft_update(
                kwargs["pool_id"],
                kwargs.get("verbose_name"),
                kwargs.get("keep_vms_on"),
                kwargs.get("connection_types"),
                creator,
            )
        except UniqueViolationError:
            error_msg = _local_(
                "Failed to update static pool {}. Name must be unique."
            ).format(kwargs["pool_id"])
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(error_msg, user=creator, entity=entity)
        return UpdateStaticPoolMutation(ok=ok)


class UpdateRdsPoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        verbose_name = ShortString()
        keep_vms_on = graphene.Boolean()
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene))

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, _root, _info, creator, **kwargs):

        pool_id = kwargs["pool_id"]
        connection_types = kwargs.get("connection_types")
        RdsPool.validate_conn_types(connection_types)
        await cls.validate(**kwargs)
        try:
            ok = await RdsPool.soft_update(
                pool_id,
                kwargs.get("verbose_name"),
                kwargs.get("keep_vms_on"),
                connection_types,
                creator,
            )
        except UniqueViolationError:
            error_msg = _local_(
                "Failed to update RDS pool {}. Name must be unique."
            ).format(pool_id)
            entity = {"entity_type": EntityType.POOL, "entity_uuid": pool_id}
            raise SimpleError(error_msg, user=creator, entity=entity)
        return UpdateRdsPoolMutation(ok=ok)


# --- --- --- --- ---
# Automated (Dynamic) and Guest pool mutations
class ExpandPoolMutation(graphene.Mutation, PoolValidator):
    """Запускает задачу на расширение пула."""

    class Arguments:
        pool_id = graphene.UUID(required=True)

    ok = graphene.Boolean()
    task_id = graphene.UUID()

    @classmethod
    @administrator_required
    async def mutate(cls, _root, _info, creator, pool_id):

        await cls.validate_pool_id(dict(), pool_id)

        # Check if pool already reached its total_size
        autopool = await AutomatedPool.get(pool_id)
        pool_name = (
            await Pool.select("verbose_name").where(Pool.id == pool_id).gino.scalar()
        )

        total_size_reached = await autopool.check_if_total_size_reached()
        if total_size_reached:
            raise SilentError(
                _local_(
                    "Can not expand pool {} because it reached its total_size.").format(
                    pool_name
                )
            )

        # Check if another task works on this pool
        tasks = await Task.get_tasks_associated_with_entity(
            pool_id, TaskStatus.IN_PROGRESS
        )
        if tasks:
            raise SilentError(
                _local_("Another task works on pool {}.").format(pool_name))

        task_id = await request_to_execute_pool_task(
            pool_id, PoolTaskType.POOL_EXPAND, ignore_reserve_size=True
        )

        verbose_name = await autopool.verbose_name
        description = _local_("Increase_step {}.").format(autopool.increase_step)
        await system_logger.info(
            _local_("Expansion of pool {} requested.").format(verbose_name),
            user=creator,
            entity=autopool.entity,
            description=description,
        )
        return {"ok": True, "task_id": task_id}


class CreateAutomatedPoolMutation(graphene.Mutation, PoolValidator, ControllerFetcher):
    class Arguments:
        controller_id = graphene.UUID(required=True)
        resource_pool_id = graphene.UUID(required=True)
        datapool_id = graphene.UUID(required=True)
        template_id = graphene.UUID(required=True)

        verbose_name = ShortString(required=True)
        increase_step = graphene.Int(default_value=1, description="Шаг расширения пула")
        initial_size = graphene.Int(
            default_value=1, description="Начальное количество ВМ"
        )
        reserve_size = graphene.Int(
            default_value=1, description="Пороговое количество свободных ВМ"
        )
        total_size = graphene.Int(
            default_value=2, description="Максимальное количество создаваемых ВМ"
        )
        vm_name_template = ShortString(required=True)

        create_thin_clones = graphene.Boolean(default_value=True)
        enable_vms_remote_access = graphene.Boolean(default_value=True)
        start_vms = graphene.Boolean(default_value=True)
        set_vms_hostnames = graphene.Boolean(default_value=False)
        include_vms_in_ad = graphene.Boolean(default_value=False)
        connection_types = graphene.List(
            graphene.NonNull(ConnectionTypesGraphene),
            default_value=[Pool.PoolConnectionTypes.SPICE.value],
        )
        ad_ou = ShortString(
            description="Наименование организационной единицы для добавления ВМ в AD"
        )
        is_guest = graphene.Boolean(default_value=False)
        waiting_time = graphene.Int()

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(
        cls,
        root,
        info,
        creator,
        controller_id,
        resource_pool_id,
        datapool_id,
        template_id,
        verbose_name,
        increase_step,
        initial_size,
        reserve_size,
        total_size,
        vm_name_template,
        create_thin_clones,
        enable_vms_remote_access,
        start_vms,
        set_vms_hostnames,
        include_vms_in_ad,
        connection_types,
        ad_ou: str = None,
        is_guest: bool = False,
        waiting_time: int = None
    ):
        """Мутация создания Автоматического(Динамического) пула виртуальных машин."""
        await cls.validate(vm_name_template=vm_name_template, verbose_name=verbose_name)
        # Создание записей в БД
        try:
            controller = await cls.fetch_by_id(controller_id)
            tag = await Pool.tag_create(
                controller=controller, verbose_name=verbose_name, creator=creator
            )

            automated_pool = await AutomatedPool.soft_create(
                creator=creator,
                verbose_name=verbose_name,
                controller_id=controller_id,
                resource_pool_id=resource_pool_id,
                datapool_id=datapool_id,
                template_id=template_id,
                increase_step=increase_step,
                initial_size=initial_size,
                reserve_size=reserve_size,
                total_size=total_size,
                vm_name_template=vm_name_template,
                create_thin_clones=create_thin_clones,
                enable_vms_remote_access=enable_vms_remote_access,
                start_vms=start_vms,
                set_vms_hostnames=set_vms_hostnames,
                include_vms_in_ad=include_vms_in_ad,
                connection_types=connection_types,
                ad_ou=ad_ou,
                tag=tag,
                is_guest=is_guest,
                waiting_time=waiting_time
            )
        except UniqueViolationError as ex:
            error_msg = _local_("Failed to create pool {}.").format(verbose_name)
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(error_msg, description=str(ex), user=creator, entity=entity)

        # send command to start pool init task
        await request_to_execute_pool_task(
            str(automated_pool.id), PoolTaskType.POOL_CREATE
        )

        # pool creation task successfully started
        pool = await Pool.get_pool(automated_pool.id)
        return CreateAutomatedPoolMutation(pool=pool_obj_to_type(pool), ok=True)


class UpdateAutomatedPoolMutation(graphene.Mutation, PoolValidator):
    """Перечень полей доступных для редактирования отдельно не рассматривалась. Перенесена логика из Confluence."""

    class Arguments:
        pool_id = graphene.UUID(required=True)
        verbose_name = ShortString()
        reserve_size = graphene.Int()
        total_size = graphene.Int()
        increase_step = graphene.Int()
        vm_name_template = ShortString()
        keep_vms_on = graphene.Boolean()
        create_thin_clones = graphene.Boolean()
        enable_vms_remote_access = graphene.Boolean()
        start_vms = graphene.Boolean()
        set_vms_hostnames = graphene.Boolean()
        include_vms_in_ad = graphene.Boolean()
        ad_ou = ShortString()
        waiting_time = graphene.Int()
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene))

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        automated_pool = await AutomatedPool.get(kwargs["pool_id"])
        if automated_pool:
            # total_size опасно уменьшать, так как в это время может выполняться задача расширения пула, что может
            # привести к тому, что в пуле будет больше машин, чем total_size (максимальное число машин)
            # Поэтому передаем задачу пул воркеру, который уменьшит total_size, только если получит соответствующий
            # пулу лок
            new_total_size = kwargs.get("total_size")
            if new_total_size and new_total_size < automated_pool.total_size:
                task_id = await request_to_execute_pool_task(
                    kwargs["pool_id"],
                    PoolTaskType.POOL_DECREASE,
                    new_total_size=new_total_size,
                )
                status = await wait_for_task_result(task_id, wait_timeout=3)

                if status is None or status != TaskStatus.FINISHED.name:
                    error_msg = _local_("Failed to update total_size. Task status is {}. "
                                        "Check journal for more info.").format(status)
                    entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
                    raise SimpleError(error_msg, user=creator, entity=entity)

                new_total_size = None

            # При изменении vm_name_template необходимо изменить имена ВМ и имена хостов ВМ
            vm_name_template = kwargs.get("vm_name_template")
            if vm_name_template != automated_pool.vm_name_template:

                pool = await Pool.get(kwargs["pool_id"])
                vms = await pool.get_vms()
                await asyncio.gather(
                    *[
                        vm_object.set_verbose_name(vm_name_template)
                        for vm_object in vms
                    ],
                    return_exceptions=True
                )

            # other params
            try:
                await automated_pool.soft_update(
                    verbose_name=kwargs.get("verbose_name"),
                    reserve_size=kwargs.get("reserve_size"),
                    total_size=new_total_size,
                    increase_step=kwargs.get("increase_step"),
                    vm_name_template=vm_name_template,
                    keep_vms_on=kwargs.get("keep_vms_on"),
                    create_thin_clones=kwargs.get("create_thin_clones"),
                    enable_vms_remote_access=kwargs.get("enable_vms_remote_access"),
                    start_vms=kwargs.get("start_vms"),
                    set_vms_hostnames=kwargs.get("set_vms_hostnames"),
                    include_vms_in_ad=kwargs.get("include_vms_in_ad"),
                    ad_ou=kwargs.get("ad_ou"),
                    waiting_time=kwargs.get("waiting_time"),
                    connection_types=kwargs.get("connection_types"),
                    creator=creator,
                )
            except UniqueViolationError:
                error_msg = _local_(
                    "Failed to update pool {}. Name must be unique."
                ).format(kwargs["verbose_name"])
                entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
                raise SimpleError(error_msg, user=creator, entity=entity)
            else:
                return UpdateAutomatedPoolMutation(ok=True)
        return UpdateAutomatedPoolMutation(ok=False)


class CopyAutomatedPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)

    pool_settings = graphene.JSONString()

    @administrator_required
    async def mutate(self, _info, pool_id, creator):
        simple_pool = await Pool.query.where(Pool.id == pool_id).gino.first()
        auto_pool = await AutomatedPool.query.where(AutomatedPool.id == pool_id).gino.first()
        pool_settings = {**simple_pool.__values__, **auto_pool.__values__}
        for key, val in pool_settings.items():
            if isinstance(val, UUID):
                pool_settings[key] = str(val)
            elif isinstance(val, Pool.PoolTypes):
                pool_settings[key] = val.value
            elif isinstance(val, Status):
                pool_settings[key] = val.value
            elif isinstance(val, list):
                pool_settings[key] = [element.value for element in val]
        await system_logger.info(_local_("Settings of pool {} is copied.").format(simple_pool.verbose_name),
                                 description=str(pool_settings),
                                 user=creator)
        return CopyAutomatedPoolMutation(pool_settings=pool_settings)


class RemoveVmsFromPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    ok = graphene.Boolean()
    task_id = graphene.ID()

    @administrator_required
    async def mutate(self, _info, pool_id, vm_ids, creator):
        vm_str_ids = [str(vm_id) for vm_id in vm_ids]
        task_id = await request_to_execute_pool_task(str(pool_id),
                                                     PoolTaskType.VMS_REMOVE,
                                                     vm_ids=vm_str_ids,
                                                     creator=creator)

        return RemoveVmsFromPoolMutation(ok=True, task_id=task_id)


# --- --- --- --- ---
# pools <-> users relations
class PoolUserAddPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        users = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, users, creator):
        pool = await Pool.get(pool_id)
        if not pool:
            return {"ok": False}

        await pool.add_users(users, creator=creator)
        pool_record = await Pool.get_pool(pool.id)

        return PoolUserAddPermissionsMutation(
            ok=True, pool=pool_obj_to_type(pool_record)
        )


class PoolUserDropPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        users = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))
        free_assigned_vms = graphene.Boolean()

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(
        self, _info, pool_id, users, free_assigned_vms=True, creator="system"
    ):
        pool = await Pool.get(pool_id)
        if not pool:
            return PoolUserDropPermissionsMutation(ok=False)

        async with db.transaction():
            await pool.remove_users(creator=creator, users_list=users)
            if free_assigned_vms:
                await pool.free_assigned_vms(users)

        pool_record = await Pool.get_pool(pool.id)
        return PoolUserDropPermissionsMutation(
            ok=True, pool=pool_obj_to_type(pool_record)
        )


class PoolGroupAddPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        groups = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, groups, creator):
        pool = await Pool.get(pool_id)
        if not pool:
            return {"ok": False}

        await pool.add_groups(creator, groups)

        pool_record = await Pool.get_pool(pool.id)
        return PoolGroupAddPermissionsMutation(
            ok=True, pool=pool_obj_to_type(pool_record)
        )


class PoolGroupDropPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        groups = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, groups, creator):
        pool = await Pool.get(pool_id)
        if not pool:
            return {"ok": False}

        await pool.remove_groups(creator, groups)

        pool_record = await Pool.get_pool(pool.id)
        return PoolGroupDropPermissionsMutation(
            ok=True, pool=pool_obj_to_type(pool_record)
        )


class AssignVmToUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)
        username = ShortString()  # Legacy
        users = graphene.List(graphene.NonNull(graphene.UUID))

    ok = graphene.Boolean()
    vm = graphene.Field(VmType)

    @administrator_required
    async def mutate(self, _info, vm_id, username=None, users=None, creator="system"):

        # Ранее назначение происходило по имени пользователя, далее был добавлено user_id.
        # Использовать либо username, либо user_id.
        # Если указаны оба, то учитывается только user_id. Не указано ничего - возвращается ошибка.

        # find pool the vm belongs to
        vm = await Vm.get(vm_id)
        if not vm:
            raise SimpleError(_local_("There is no VM {}.").format(vm_id))

        pool_id = vm.pool_id

        if pool_id:
            pool = await Pool.get(pool_id)
            # Если пул гостевой и ВМ уже имеет пользователя, то возвращаем ошибку. Назначение ВМ
            # больше одного пользовтеля не имеет смысл, так как в гостевом пуле ВМ
            # будет удалена после отключения от нее любого пользователя.
            users_count = await vm.get_users_count()
            if pool.pool_type == Pool.PoolTypes.GUEST and users_count > 0:
                raise SimpleError(
                    _local_("Impossible to assign more than 1 user to VM {} in guest pool.").format(vm.verbose_name))

            if username:
                users = list()
                user_id = await User.get_id(username)
                users.append(user_id)
            elif not users and not username:
                raise SimpleError(_local_("Provide users list or username."))

            for user in users:
                # check if the user is entitled to the pool(pool_id) the vm belongs to
                user_entitled_to_pool = await pool.check_if_user_assigned(user)

                if not user_entitled_to_pool:
                    # Requested user is not entitled to the pool the requested vm belongs to
                    raise SimpleError(
                        _local_("User does not have the right to use pool, which has VM.")
                    )

                # another vm in the pool may have this user as owner. Remove assignment
                await pool.free_user_vms(user)

                await vm.add_user(user, creator)
            return AssignVmToUser(ok=True, vm=vm)
        return AssignVmToUser(ok=False, vm=vm)


class FreeVmFromUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)
        username = ShortString()
        users = graphene.List(graphene.NonNull(graphene.UUID))

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, username=None, users=None, creator="system"):
        vm = await Vm.get(vm_id)
        if vm:
            if username:
                users = list()
                user_id = await User.get_id(username)
                users.append(user_id)
            elif not users and not username:
                raise SimpleError(_local_("Provide users list or username."))
            await vm.remove_users(creator=creator, users_list=users)
            return FreeVmFromUser(ok=True)
        return FreeVmFromUser(ok=False)


class ReserveVm(graphene.Mutation):
    class Arguments:
        vm_id = graphene.UUID(required=True)
        reserve = graphene.Boolean(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, reserve=True, creator="system"):
        vm = await Vm.get(vm_id)
        if vm:
            await vm.reserve(creator=creator, reserve=reserve)
            return ReserveVm(ok=True)
        return ReserveVm(ok=False)


class PrepareVm(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, **kwargs):

        # Проверить есть ли в таблице task таски выполняющиеся над этой вм. Если есть то сообщить фронту
        # что подготовка вм уже идет
        tasks = await Task.get_tasks_associated_with_entity(
            vm_id, TaskStatus.IN_PROGRESS
        )
        if tasks:
            vm = await Vm.get(vm_id)
            raise SilentError(
                _local_("Another task works on VM {}.").format(vm.verbose_name))

        await Entity.create(entity_uuid=vm_id, entity_type=EntityType.VM)
        await request_to_execute_pool_task(vm_id, PoolTaskType.VM_PREPARE)
        return PrepareVm(ok=True)


class VmStart(graphene.Mutation):
    class Arguments:
        vm_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, creator, **kwargs):
        vm = await Vm.get(vm_id)
        if vm:
            domain_entity = await vm.vm_client
            if not domain_entity:
                return
            await domain_entity.info()
            asyncio.ensure_future(vm.start(creator=creator))
            return VmStart(ok=True)
        return VmStart(ok=False)


class VmShutdown(graphene.Mutation):
    class Arguments:
        vm_id = graphene.UUID(required=True)
        force = graphene.Boolean(default_value=False)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, force, creator, **kwargs):
        vm = await Vm.get(vm_id)
        if vm:
            domain_entity = await vm.vm_client
            if not domain_entity:
                return
            await domain_entity.info()
            asyncio.ensure_future(vm.shutdown(creator=creator, force=force))
            return VmShutdown(ok=True)
        return VmShutdown(ok=False)


class VmReboot(graphene.Mutation):
    class Arguments:
        vm_id = graphene.UUID(required=True)
        force = graphene.Boolean(default_value=False)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, force, creator, **kwargs):
        vm = await Vm.get(vm_id)
        if vm:
            domain_entity = await vm.vm_client
            if not domain_entity:
                return
            await domain_entity.info()
            asyncio.ensure_future(vm.reboot(creator=creator, force=force))
            return VmReboot(ok=True)
        return VmReboot(ok=False)


class VmSuspend(graphene.Mutation):
    class Arguments:
        vm_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, creator, **kwargs):
        vm = await Vm.get(vm_id)
        if vm:
            domain_entity = await vm.vm_client
            if not domain_entity:
                return
            await domain_entity.info()
            asyncio.ensure_future(vm.suspend(creator=creator))
            return VmSuspend(ok=True)
        return VmSuspend(ok=False)


class VmBackup(graphene.Mutation):
    class Arguments:
        vm_id = graphene.UUID(required=True)

    ok = graphene.Boolean()
    task_id = graphene.ID()

    @administrator_required
    async def mutate(self, _info, vm_id, creator, **kwargs):

        task_id = await request_to_execute_pool_task(
            vm_id,
            PoolTaskType.VMS_BACKUP,
            entity_type=EntityType.VM.name,
            creator=creator,
        )
        return VmBackup(ok=True, task_id=task_id)


class PoolVmsBackup(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        multiple_tasks = graphene.Boolean(default_value=True)

    ok = graphene.Boolean()
    task_ids = graphene.List(graphene.UUID)

    @administrator_required
    async def mutate(self, _info, pool_id, multiple_tasks, creator, **kwargs):

        task_ids = []
        # Launch task for every vm
        if multiple_tasks:
            pool = await Pool.get(pool_id)
            vms = await pool.get_vms()
            for vm in vms:
                task_id = await request_to_execute_pool_task(
                    vm.id,
                    PoolTaskType.VMS_BACKUP,
                    entity_type=EntityType.VM.name,
                    creator=creator,
                )
                task_ids.append(task_id)
        # one task
        else:
            task_id = await request_to_execute_pool_task(
                pool_id,
                PoolTaskType.VMS_BACKUP,
                entity_type=EntityType.POOL.name,
                creator=creator,
            )
            task_ids.append(task_id)
        return PoolVmsBackup(ok=True, task_ids=task_ids)


class VmTestDomain(graphene.Mutation):
    """Проверка нахождения ВМ в домене."""

    class Arguments:
        vm_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, creator, **kwargs):
        vm = await Vm.get(vm_id)
        if vm:
            domain_entity = await vm.vm_client
            await domain_entity.info()
            if domain_entity.os_windows:
                ok = await domain_entity.is_in_ad()
                return VmTestDomain(ok=ok)
        raise SilentError(_local_("Only VM with Windows OS can be in domain."))


class VmRestoreBackup(graphene.Mutation):
    """Восстановление ВМ из бэкапа."""

    class Arguments:
        vm_id = graphene.UUID(required=True)
        file_id = graphene.UUID(required=True)
        node_id = graphene.UUID(required=True)
        datapool_id = graphene.UUID()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(
        self, _info, vm_id, file_id, node_id, creator, datapool_id=None, **kwargs
    ):
        vm = await Vm.get(vm_id)
        ok = asyncio.ensure_future(
            vm.restore_backup(
                file_id=file_id,
                node_id=node_id,
                datapool_id=datapool_id,
                creator=creator,
            )
        )
        return VmRestoreBackup(ok=ok)


class AttachVeilUtilsMutation(graphene.Mutation):
    """Монтирование образа veil utils к ВМ в пуле."""

    class Arguments:
        vm_id = graphene.UUID(required=True)
        controller_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, vm_id, controller_id, creator):
        controller = await Controller.get(controller_id)
        veil_domain = controller.veil_client.domain(domain_id=str(vm_id))
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


class TemplateChange(graphene.Mutation):
    """Мутация для ВМ, которая внесет изменения текущей ВМ во все тонкие клоны через изменение шаблона."""

    class Arguments:
        vm_id = graphene.UUID(required=True)
        controller_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, vm_id, controller_id, creator):
        controller = await Controller.get(controller_id)
        veil_domain = controller.veil_client.domain(domain_id=str(vm_id))
        await veil_domain.info()
        if veil_domain.powered:
            raise SilentError(
                _local_("VM {} is powered. Please shutdown this.").format(
                    veil_domain.public_attrs["verbose_name"]))
        response = await veil_domain.change_template()
        ok = response.success
        if not ok:
            for error in response.errors:
                raise SilentError(
                    _local_("VeiL ECP error: {}.").format(error["detail"]))

        await system_logger.info(
            _local_(
                "The template {} change and distribute this changes to thin clones.").format(
                veil_domain.parent_name),
            user=creator)
        return TemplateChange(ok=ok)


class VmConvertToTemplate(graphene.Mutation, PoolValidator):
    """Мутация для ВМ, которая конвертирует ВМ в шаблон."""

    class Arguments:
        verbose_name = ShortString(required=True)
        vm_id = graphene.UUID(required=True)
        controller_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, verbose_name, vm_id, controller_id, creator):
        await cls.validate(vm_name_template=verbose_name)

        controller = await Controller.get(controller_id)
        veil_domain = controller.veil_client.domain(domain_id=str(vm_id))
        await veil_domain.info()
        if veil_domain.powered:
            raise SilentError(
                _local_("VM {} is powered. Please shutdown this.").format(
                    veil_domain.public_attrs["verbose_name"]))
        params = {
            "verbose_name": verbose_name,
            "domain_id": veil_domain.id,
            "resource_pool_id": str(veil_domain.resource_pool["id"]),
            "controller_id": controller_id,
            "create_thin_clones": False,
            "count": 1
        }
        if veil_domain.thin:
            raise SilentError(
                _local_("Prohibited creating template from the thin clone."))

        vm_info = await Vm.copy(**params)

        # Ожидаем завершения таски создания ВМ
        task = controller.veil_client.task(task_id=vm_info["task_id"])
        await VeilModel.task_waiting(task)

        new_vm_id = vm_info["ids"][0]
        veil_new_vm = controller.veil_client.domain(domain_id=str(new_vm_id))
        response = await veil_new_vm.convert_to_template()

        ok = response.success
        if not ok:
            for error in response.errors:
                raise SilentError(
                    _local_("VeiL ECP error: {}.").format(error["detail"]))

        await system_logger.info(
            _local_("Vm {} has converted to template {}.").format(
                veil_domain.verbose_name, verbose_name),
            user=creator)
        return VmConvertToTemplate(ok=ok)


# --- --- --- --- ---
# Schema concatenation
class PoolMutations(graphene.ObjectType):
    addDynamicPool = CreateAutomatedPoolMutation.Field()
    addStaticPool = CreateStaticPoolMutation.Field()
    addRdsPool = CreateRdsPoolMutation.Field()
    addVmsToStaticPool = AddVmsToStaticPoolMutation.Field()
    removeVmsFromStaticPool = RemoveVmsFromPoolMutation.Field()
    removeVmsFromDynamicPool = RemoveVmsFromPoolMutation.Field()
    removePool = DeletePoolMutation.Field()
    updateDynamicPool = UpdateAutomatedPoolMutation.Field()
    copyDynamicPool = CopyAutomatedPoolMutation.Field()
    updateStaticPool = UpdateStaticPoolMutation.Field()
    updateRdsPool = UpdateRdsPoolMutation.Field()
    expandPool = ExpandPoolMutation.Field()
    clearPool = ClearPoolMutation.Field()

    entitleUsersToPool = PoolUserAddPermissionsMutation.Field()
    removeUserEntitlementsFromPool = PoolUserDropPermissionsMutation.Field()
    addPoolGroup = PoolGroupAddPermissionsMutation.Field()
    removePoolGroup = PoolGroupDropPermissionsMutation.Field()

    # Vm mutations
    assignVmToUser = AssignVmToUser.Field()
    freeVmFromUser = FreeVmFromUser.Field()
    prepareVm = PrepareVm.Field()
    startVm = VmStart.Field()
    shutdownVm = VmShutdown.Field()
    rebootVm = VmReboot.Field()
    suspendVm = VmSuspend.Field()
    backupVm = VmBackup.Field()
    backupVms = PoolVmsBackup.Field()
    testDomainVm = VmTestDomain.Field()
    restoreBackupVm = VmRestoreBackup.Field()
    attachVeilUtilsVm = AttachVeilUtilsMutation.Field()
    changeTemplate = TemplateChange.Field()
    convertToTemplate = VmConvertToTemplate.Field()
    reserveVm = ReserveVm.Field()


pool_schema = graphene.Schema(
    query=PoolQuery, mutation=PoolMutations, auto_camelcase=False
)
