# -*- coding: utf-8 -*-
import asyncio
import re

from asyncpg.exceptions import UniqueViolationError

import graphene

from common.database import db
from common.languages import lang_init
from common.log.journal import system_logger
from common.models.auth import Entity, User
from common.models.controller import Controller
from common.models.pool import AutomatedPool, Pool, StaticPool
from common.models.task import PoolTaskType, Task, TaskStatus
from common.models.vm import Vm
from common.settings import POOL_MAX_SIZE, POOL_MIN_SIZE
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SilentError, SimpleError, ValidationError
from common.veil.veil_gino import (
    EntityType,
    Role,
    RoleTypeGraphene,
    Status,
    StatusGraphene,
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

_ = lang_init()

# TODO: отсутствует валидация входящих ресурсов вроде node_uid, cluster_uid и т.п. Ранее шла речь,
#  о том, что мы будем кешированно хранить какие-то ресурсы полученные от ECP Veil. Возможно стоит
#  обращаться к этому хранилищу для проверки корректности присланных ресурсов. Аналогичный принцип
#  стоит применить и к статическим пулам (вместо похода на вейл для проверки присланных параметров).

ConnectionTypesGraphene = graphene.Enum.from_enum(Pool.PoolConnectionTypes)


class ControllerFetcher:
    # TODO: временное дублирование

    @staticmethod
    async def fetch_by_id(id_):
        """Возваращает инстанс объекта, если он есть."""
        # TODO: универсальный метод в родительском валидаторе для сокращения дублированияа
        controller = await Controller.get(id_)
        if not controller:
            raise SimpleError(_("No such controller."))
        return controller

    @staticmethod
    async def fetch_all(status=Status.ACTIVE):
        """Возвращает все записи контроллеров в определенном статусе."""
        return await Controller.query.where(Controller.status == status).gino.all()


class VmBackupType(VeilResourceType):
    filename = graphene.String()
    size = graphene.Int()
    assignment_type = graphene.String()
    datapool = graphene.Field(ResourceDataPoolType)
    status = StatusGraphene()


class VmType(VeilResourceType):
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
    user_power_state = VmState(description="Питание")
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
    parent_name = graphene.String(description="Родительская ВМ")
    hostname = graphene.String()
    address = graphene.List(graphene.String)
    domain_tags = graphene.List(VeilTagsType)
    user = graphene.Field(UserType)
    # controller = graphene.Field(ControllerType)
    # qemu_state = graphene.Boolean(description='Состояние гостевого агента')
    qemu_state = VmState(description="Состояние гостевого агента")
    backups = graphene.List(VmBackupType)

    # Список событий для отдельной ВМ и отдельное событие внутри пула
    count = graphene.Int()
    events = graphene.List(
        EventType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )
    event = graphene.Field(EventType, event_id=graphene.UUID())

    async def resolve_user(self, _info):
        vm = await Vm.get(self.id)
        username = await vm.username if vm else None
        return UserType(username=username)

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
        domain_entity = await vm_obj.get_veil_entity()
        await domain_entity.info()
        # Список бэкапов ВМ
        response = await domain_entity.backup_list()
        veil_backups_list = list()
        backups_list = list()
        for data in response.response:
            backup = data.public_attrs
            backups_list.append(backup)

        for data in backups_list:
            veil_backups_list.append(VmBackupType(**data))

        return veil_backups_list


class VmInput(graphene.InputObjectType):
    """Инпут для ввода ВМ."""

    id = graphene.UUID()
    verbose_name = graphene.String()


class PoolValidator(MutationValidation):
    """Валидатор для сущности Pool."""

    @staticmethod
    async def validate_pool_id(obj_dict, value):
        if not value:
            return
        pool = await Pool.get_pool(value)
        if pool:
            return value
        raise ValidationError(_("No such pool."))

    @staticmethod
    async def validate_verbose_name(obj_dict, value):
        if not value:
            return
        name_re = re.compile("^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$")
        template_name = re.match(name_re, value)
        if template_name:
            return value
        raise ValidationError(
            _("Pool name must contain only characters, digits, _, -.")
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
            _(
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
                _("Initial number of VM must be in {}-{} interval.").format(
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
                _("Reserve size of VMs can not be more than maximal number of Vms.")
            )

        if value < POOL_MIN_SIZE or value > POOL_MAX_SIZE:
            raise ValidationError(
                _("Reserve size of VM must be in {}-{} interval.").format(
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
                _(
                    "Maximal number of created VM can not be less than initial number of VM."
                )
            )
        if value < POOL_MIN_SIZE or value > POOL_MAX_SIZE:
            raise ValidationError(
                _("Maximal number of created VM must be in [{} {}] interval.").format(
                    POOL_MIN_SIZE, POOL_MAX_SIZE
                )
            )
        if vm_amount_in_pool and value < vm_amount_in_pool:
            raise ValidationError(
                _(
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
                _("Increase step must be positive and less or equal to total_size.")
            )
        return value

    @staticmethod
    async def validate_connection_types(obj_dict, value):
        if not value:
            raise ValidationError(_("Connection type cannot be empty."))


class PoolGroupType(graphene.ObjectType):
    """Намеренное дублирование UserGroupType и GroupType +с сокращением доступных полей.

    Нет понимания в целесообразности абстрактного класса для обоих типов.
    """

    id = graphene.UUID(required=True)
    verbose_name = graphene.String()
    description = graphene.String()

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
    verbose_name = graphene.String()
    status = StatusGraphene()
    pool_type = graphene.String()
    resource_pool_id = graphene.UUID()
    controller = graphene.Field(ControllerType)
    vm_amount = graphene.Int()

    # StaticPool fields
    static_pool_id = graphene.UUID()

    # AutomatedPool fields
    automated_pool_id = graphene.UUID()
    template_id = graphene.UUID()
    increase_step = graphene.Int()
    max_amount_of_create_attempts = graphene.Int()
    initial_size = graphene.Int()
    reserve_size = graphene.Int()
    total_size = graphene.Int()
    vm_name_template = graphene.String()
    os_type = graphene.String()
    ad_cn_pattern = graphene.String()

    users = graphene.List(UserType, entitled=graphene.Boolean())
    assigned_roles = graphene.List(RoleTypeGraphene)
    possible_roles = graphene.List(RoleTypeGraphene)
    assigned_groups = graphene.List(
        PoolGroupType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )
    possible_groups = graphene.List(PoolGroupType)

    keep_vms_on = graphene.Boolean()
    create_thin_clones = graphene.Boolean()
    prepare_vms = graphene.Boolean()
    assigned_connection_types = graphene.List(ConnectionTypesGraphene)
    possible_connection_types = graphene.List(ConnectionTypesGraphene)

    # Затрагивает запрос ресурсов на VeiL ECP.
    template = graphene.Field(VeilShortEntityType)
    resource_pool = graphene.Field(VeilShortEntityType)
    vms = graphene.List(VmType)
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

    async def resolve_assigned_groups(self, info, limit, offset):
        pool = await Pool.get(self.pool_id)
        return await pool.assigned_groups_paginator(limit=limit, offset=offset)

    async def resolve_possible_groups(self, _info):
        pool = await Pool.get(self.pool_id)
        return await pool.possible_groups

    async def resolve_users(self, _info, entitled=True):
        # TODO: добавить пагинацию
        pool = await Pool.get(self.pool_id)
        return await pool.assigned_users if entitled else await pool.possible_users

    async def resolve_vms(self, _info):
        # TODO: добавить пагинацию
        pool = await Pool.get(self.pool_id)
        vms_info = await pool.get_vms_info()

        # TODO: получить список ВМ и статусов
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
                data["address"] = veil_domain.guest_agent.ipv4
            return VmType(**data)
        else:
            raise SilentError(_("VM is unreachable on ECP VeiL."))

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
        "pool_type": pool_obj.pool_type,
        "resource_pool_id": pool_obj.resource_pool_id,
        "static_pool_id": pool_obj.master_id,
        "automated_pool_id": pool_obj.master_id,
        "template_id": pool_obj.template_id,
        "increase_step": pool_obj.increase_step,
        "max_amount_of_create_attempts": pool_obj.max_amount_of_create_attempts,
        "initial_size": pool_obj.initial_size,
        "reserve_size": pool_obj.reserve_size,
        "total_size": pool_obj.total_size,
        "vm_name_template": pool_obj.vm_name_template,
        "os_type": pool_obj.os_type,
        "keep_vms_on": pool_obj.keep_vms_on,
        "ad_cn_pattern": pool_obj.ad_cn_pattern,
        "create_thin_clones": pool_obj.create_thin_clones,
        "prepare_vms": pool_obj.prepare_vms,
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
        ordering=graphene.String(),
    )
    pool = graphene.Field(PoolType, pool_id=graphene.String())

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
            raise SimpleError(_("No such pool."), entity=entity)
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
            raise SimpleError(_("No such pool."), entity=entity)

        try:
            pool_type = await pool.pool_type

            # Авто пул
            if pool_type == Pool.PoolTypes.AUTOMATED:
                await execute_delete_pool_task(
                    str(pool.id), full=full, wait_for_result=False
                )
                return DeletePoolMutation(ok=True)
            else:
                is_deleted = await Pool.delete_pool(pool, creator)
                return DeletePoolMutation(ok=is_deleted)
        except Exception as e:
            raise e


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
        verbose_name = graphene.String(required=True)
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
                controller_address=controller.address,
                connection_types=connection_types,
                tag=tag,
                creator=creator,
            )
        except Exception as E:  # Возможные исключения: дубликат имени или вм id, сетевой фейл enable_remote_accesses
            # TODO: указать конкретные Exception
            desc = str(E)
            error_msg = _("Failed to create static pool {}.").format(verbose_name)
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
                    _("VM {} is already in one of pools.").format(vm_id), entity=entity
                )

        # TODO: использовать нормальный набор данных с verbose_name и id
        # Add VMs to db
        for vm in vms:
            await Vm.create(
                id=vm.id,
                template_id=None,
                pool_id=pool_id,
                created_by_vdi=False,
                verbose_name=vm.verbose_name,
            )
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            await system_logger.info(
                _("VM {} has been added to the pool {}.").format(
                    vm.verbose_name, pool.verbose_name
                ),
                user=creator,
                entity=entity,
            )

            if pool.tag:
                await pool.tag_add_entity(
                    tag=pool.tag, entity_id=vm.id, verbose_name=vm.verbose_name
                )

            # Запустить задачи подготовки машин
            await request_to_execute_pool_task(
                vm.id, PoolTaskType.VM_PREPARE, full=False
            )

        return {"ok": True}


class RemoveVmsFromStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, pool_id, vm_ids, creator):
        pool = await Pool.get(pool_id)
        await pool.remove_vms(vm_ids, creator)

        # remove vms from db
        await Vm.remove_vms(vm_ids, creator)

        return {"ok": True}


class UpdateStaticPoolMutation(graphene.Mutation, PoolValidator):
    """ """

    class Arguments:
        pool_id = graphene.UUID(required=True)
        verbose_name = graphene.String()
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
            error_msg = _(
                "Failed to update static pool {}. Name must be unique."
            ).format(kwargs["pool_id"])
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(error_msg, user=creator, entity=entity)
        return UpdateStaticPoolMutation(ok=ok)


# --- --- --- --- ---
# Automated (Dynamic) pool mutations
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
                _("Can not expand pool {} because it reached its total_size.").format(
                    pool_name
                )
            )

        # Check if another task works on this pool
        tasks = await Task.get_tasks_associated_with_entity(
            pool_id, TaskStatus.IN_PROGRESS
        )
        if tasks:
            raise SilentError(_("Another task works on pool {}.").format(pool_name))

        task_id = await request_to_execute_pool_task(
            pool_id, PoolTaskType.POOL_EXPAND, ignore_reserve_size=True
        )

        verbose_name = await autopool.verbose_name
        description = _("Increase_step {}.").format(autopool.increase_step)
        await system_logger.info(
            _("Expansion of pool {} requested.").format(verbose_name),
            user=creator,
            entity=autopool.entity,
            description=description,
        )
        return {"ok": True, "task_id": task_id}


class CreateAutomatedPoolMutation(graphene.Mutation, PoolValidator, ControllerFetcher):
    class Arguments:
        controller_id = graphene.UUID(required=True)
        resource_pool_id = graphene.UUID(required=True)
        template_id = graphene.UUID(required=True)

        verbose_name = graphene.String(required=True)
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
        vm_name_template = graphene.String(required=True)

        create_thin_clones = graphene.Boolean(default_value=True)
        prepare_vms = graphene.Boolean(default_value=True)
        connection_types = graphene.List(
            graphene.NonNull(ConnectionTypesGraphene),
            default_value=[Pool.PoolConnectionTypes.SPICE.value],
        )
        ad_cn_pattern = graphene.String(
            description="Наименование групп для добавления ВМ в AD"
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
        template_id,
        verbose_name,
        increase_step,
        initial_size,
        reserve_size,
        total_size,
        vm_name_template,
        create_thin_clones,
        prepare_vms,
        connection_types,
        ad_cn_pattern: str = None,
    ):
        """Мутация создания Автоматического(Динамического) пула виртуальных машин."""
        controller = await cls.fetch_by_id(controller_id)
        # TODO: дооживить валидатор
        await cls.validate(vm_name_template=vm_name_template, verbose_name=verbose_name)
        # Создание записей в БД
        try:
            tag = await Pool.tag_create(
                controller=controller, verbose_name=verbose_name, creator=creator
            )

            automated_pool = await AutomatedPool.soft_create(
                creator=creator,
                verbose_name=verbose_name,
                controller_ip=controller.address,
                resource_pool_id=resource_pool_id,
                template_id=template_id,
                increase_step=increase_step,
                initial_size=initial_size,
                reserve_size=reserve_size,
                total_size=total_size,
                vm_name_template=vm_name_template,
                create_thin_clones=create_thin_clones,
                prepare_vms=prepare_vms,
                connection_types=connection_types,
                ad_cn_pattern=ad_cn_pattern,
                tag=tag,
            )
        except Exception as E:  # Возможные исключения: дубликат имени вм
            desc = str(E)
            error_msg = _("Failed to create automated pool {}.").format(verbose_name)
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(error_msg, description=desc, user=creator, entity=entity)

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
        verbose_name = graphene.String()
        reserve_size = graphene.Int()
        total_size = graphene.Int()
        increase_step = graphene.Int()
        vm_name_template = graphene.String()
        keep_vms_on = graphene.Boolean()
        create_thin_clones = graphene.Boolean()
        prepare_vms = graphene.Boolean()
        ad_cn_pattern = graphene.String()
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
                    error_msg = "Failed to update total_size"
                    entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
                    raise SimpleError(error_msg, user=creator, entity=entity)

                new_total_size = None

            # При изменении vm_name_template необходимо изменить имена ВМ и имена хостов ВМ
            vm_name_template = kwargs.get("vm_name_template")
            if vm_name_template != automated_pool.vm_name_template:

                pool = await Pool.get(kwargs["pool_id"])
                vms = await pool.vms
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
                    prepare_vms=kwargs.get("prepare_vms"),
                    ad_cn_pattern=kwargs.get("ad_cn_pattern"),
                    connection_types=kwargs.get("connection_types"),
                    creator=creator,
                )
            except UniqueViolationError:
                error_msg = _(
                    "Failed to update automated pool {}. Name must be unique."
                ).format(kwargs["verbose_name"])
                entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
                raise SimpleError(error_msg, user=creator, entity=entity)
            else:
                return UpdateAutomatedPoolMutation(ok=True)
        return UpdateAutomatedPoolMutation(ok=False)


class RemoveVmsFromAutomatedPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, pool_id, vm_ids, creator):
        pool = await Pool.get(pool_id)
        await pool.remove_vms(vm_ids, creator)

        # remove vms from db
        await Vm.remove_vms(vm_ids, creator, True)

        return {"ok": True}


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
        username = graphene.String(required=True)  # TODO: заменить на user_id

    ok = graphene.Boolean()
    vm = graphene.Field(VmType)

    @administrator_required
    async def mutate(self, _info, vm_id, username, creator):
        # find pool the vm belongs to
        vm = await Vm.get(vm_id)
        if not vm:
            raise SimpleError(_("There is no VM {}.").format(vm_id))

        pool_id = vm.pool_id
        # TODO: заменить на user_id
        user_id = await User.get_id(username)
        # if not pool_id:
        #     # Requested vm doesnt belong to any pool
        #     raise GraphQLError('VM don\'t belongs to any Pool.')

        # check if the user is entitled to pool(pool_id) the vm belongs to
        if pool_id:
            pool = await Pool.get(pool_id)
            assigned_users = await pool.assigned_users
            assigned_users_list = [user.id for user in assigned_users]

            if user_id not in assigned_users_list:
                # Requested user is not entitled to the pool the requested vm belongs to
                raise SimpleError(
                    _("User does not have the right to use pool, which has VM.")
                )

            # another vm in the pool may have this user as owner. Remove assignment
            await pool.free_user_vms(user_id)

        # Сейчас за VM может быть только 1 пользователь. Освобождаем от других.
        await vm.remove_users(creator=creator, users_list=None)
        await vm.add_user(user_id, creator)
        return AssignVmToUser(ok=True, vm=vm)


class FreeVmFromUser(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, creator):
        vm = await Vm.get(vm_id)
        if vm:
            # await vm.free_vm()
            await vm.remove_users(creator=creator, users_list=None)
            return FreeVmFromUser(ok=True)
        return FreeVmFromUser(ok=False)


class PrepareVm(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, **kwargs):

        # Проверить есть ли в таблице task таски выполняющиеся над этой вм. Если есть то сообщить фронту ч
        # что подготовка вм уже идет
        tasks = await Task.get_tasks_associated_with_entity(
            vm_id, TaskStatus.IN_PROGRESS
        )
        if tasks:
            vm = await Vm.get(vm_id)
            raise SilentError(_("Another task works on VM {}.").format(vm.verbose_name))

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

    @administrator_required
    async def mutate(self, _info, vm_id, creator, **kwargs):

        await request_to_execute_pool_task(
            vm_id,
            PoolTaskType.VMS_BACKUP,
            entity_type=EntityType.VM.name,
            creator=creator,
        )
        return VmBackup(ok=True)


class PoolVmsBackup(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        multiple_tasks = graphene.Boolean(default_value=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, pool_id, multiple_tasks, creator, **kwargs):

        # Launch task for every vm
        if multiple_tasks:
            pool = await Pool.get(pool_id)
            vms = await pool.vms
            for vm in vms:
                await request_to_execute_pool_task(
                    vm.id,
                    PoolTaskType.VMS_BACKUP,
                    entity_type=EntityType.VM.name,
                    creator=creator,
                )
        # one task
        else:
            await request_to_execute_pool_task(
                pool_id,
                PoolTaskType.VMS_BACKUP,
                entity_type=EntityType.POOL.name,
                creator=creator,
            )
        return PoolVmsBackup(ok=True)


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
        raise SilentError(_("Only VM with Windows OS can be in domain."))


# --- --- --- --- ---
# Schema concatenation
class PoolMutations(graphene.ObjectType):
    addDynamicPool = CreateAutomatedPoolMutation.Field()
    addStaticPool = CreateStaticPoolMutation.Field()
    addVmsToStaticPool = AddVmsToStaticPoolMutation.Field()
    removeVmsFromStaticPool = RemoveVmsFromStaticPoolMutation.Field()
    removeVmsFromDynamicPool = RemoveVmsFromAutomatedPoolMutation.Field()
    removePool = DeletePoolMutation.Field()
    updateDynamicPool = UpdateAutomatedPoolMutation.Field()
    updateStaticPool = UpdateStaticPoolMutation.Field()
    expandPool = ExpandPoolMutation.Field()

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


pool_schema = graphene.Schema(
    query=PoolQuery, mutation=PoolMutations, auto_camelcase=False
)
