# -*- coding: utf-8 -*-
import asyncio
import re

import graphene
from asyncpg.exceptions import UniqueViolationError

from common.database import db
from common.veil.veil_gino import RoleTypeGraphene, Role, StatusGraphene, Status, EntityType
from common.veil.veil_validators import MutationValidation
from common.veil.veil_errors import SimpleError, ValidationError
from common.veil.veil_decorators import administrator_required
from common.veil.veil_graphene import VeilShortEntityType, VeilResourceType

from common.models.auth import User
from common.models.authentication_directory import AuthenticationDirectory
from common.models.vm import Vm
from common.models.controller import Controller
from common.models.pool import AutomatedPool, StaticPool, Pool
from common.models.task import PoolTaskType

from common.languages import lang_init
from common.log.journal import system_logger
from common.veil.veil_redis import request_to_execute_pool_task, execute_delete_pool_task

from web_app.auth.user_schema import UserType
from web_app.controller.schema import ControllerType

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
            raise SimpleError(_('No such controller.'))
        return controller

    @staticmethod
    async def fetch_all(status=Status.ACTIVE):
        """Возвращает все записи контроллеров в определенном статусе."""
        return await Controller.query.where(Controller.status == status).gino.all()


class VmType(VeilResourceType):
    verbose_name = graphene.String()
    id = graphene.String()
    user = graphene.Field(UserType)
    status = StatusGraphene()

    async def resolve_user(self, _info):
        vm = await Vm.get(self.id)
        username = await vm.username if vm else None
        return UserType(username=username)

    # TODO: перевел на показ статуса ВМ. Удалить после тестирования
    # async def resolve_status(self, _info):
    #     vm = await Vm.get(self.id)
    #     pool = await Pool.get(vm.pool_id)
    #     pool_controller = await pool.controller_obj
    #     veil_domain = pool_controller.veil_client.domain(str(self.id))
    #     await veil_domain.info()
    #     return veil_domain.status


class VmInput(graphene.InputObjectType):
    """Инпут для ввода ВМ."""

    id = graphene.UUID()
    verbose_name = graphene.String()


class PoolValidator(MutationValidation):
    """Валидатор для сущности Pool"""

    @staticmethod
    async def validate_pool_id(obj_dict, value):
        if not value:
            return
        pool = await Pool.get_pool(value)
        if pool:
            return value
        raise ValidationError(_('No such pool.'))

    @staticmethod
    async def validate_verbose_name(obj_dict, value):
        if not value:
            return
        name_re = re.compile('^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$')
        template_name = re.match(name_re, value)
        if template_name:
            return value
        raise ValidationError(_('Pool name must contain only characters, digits, _, -'))

    @staticmethod
    async def validate_vm_name_template(obj_dict, value):
        if not value:
            return

        name_re = re.compile('^[a-zA-Z]+[a-zA-Z0-9-]{2,63}$')
        template_name = re.match(name_re, value)
        if template_name:
            return value
        raise ValidationError(_('Template name of VM must contain only characters, digits, -'))

    @staticmethod
    async def validate_initial_size(obj_dict, value):
        if value is None:
            return
        if value < obj_dict['min_size'] or value > obj_dict['max_size']:
            raise ValidationError(
                _('Initial number of VM must be in {}-{} interval').format(obj_dict['min_size'], obj_dict['max_size']))
        return value

    @staticmethod
    async def validate_reserve_size(obj_dict, value):
        if value is None:
            return
        pool_id = obj_dict.get('pool_id')
        if pool_id:
            pool_obj = await Pool.get_pool(pool_id)
            min_size = obj_dict['min_size'] if obj_dict.get('min_size') else pool_obj.min_size
            max_size = obj_dict['max_size'] if obj_dict.get('max_size') else pool_obj.max_size
        else:
            min_size = obj_dict['min_size']
            max_size = obj_dict['max_size']
        if value < min_size or value > max_size:
            raise ValidationError(_('Number of created VM must be in {}-{} interval').
                                  format(min_size, max_size))
        return value

    @staticmethod
    async def validate_total_size(obj_dict, value):
        if value is None:
            return

        pool_id = obj_dict.get('pool_id')
        if pool_id:
            pool_obj = await Pool.get_pool(pool_id)
            initial_size = obj_dict['initial_size'] if obj_dict.get('initial_size') else pool_obj.initial_size
            min_size = obj_dict['min_size'] if obj_dict.get('min_size') else pool_obj.min_size
            max_vm_amount = obj_dict['max_vm_amount'] if obj_dict.get('max_vm_amount') else pool_obj.max_vm_amount
            total_size = pool_obj.total_size
        else:
            initial_size = obj_dict['initial_size']
            min_size = obj_dict['min_size']
            max_vm_amount = obj_dict['max_vm_amount']
            total_size = None

        if value < initial_size:
            raise ValidationError(_('Maximal number of created VM should be less than initial number of VM'))
        if value < min_size or value > max_vm_amount:
            raise ValidationError(_('Maximal number of created VM must be in [{} {}] interval').
                                  format(min_size, max_vm_amount))
        if total_size and value < total_size:
            raise ValidationError(_('Maximal number of created VM can not be reduced.'))
        return value

    @staticmethod
    async def validate_increase_step(obj_dict, value):
        if value is None:
            return

        total_size = obj_dict['total_size'] if obj_dict.get('total_size') else None
        if total_size is None:
            pool_id = obj_dict.get('pool_id')
            automated_pool = await AutomatedPool.get(pool_id)
            if automated_pool:
                total_size = automated_pool.total_size
        print('!!!total_size ', total_size)
        if value < 1 or value > total_size:
            raise ValidationError(_('Increase step must be positive and less or equal to total_size').
                                  format(total_size))
        return value


class PoolGroupType(graphene.ObjectType):
    """Намеренное дублирование UserGroupType и GroupType +с сокращением доступных полей.
    Нет понимания в целесообразности абстрактного класса для обоих типов."""
    id = graphene.UUID(required=True)
    verbose_name = graphene.String()
    description = graphene.String()

    @staticmethod
    def instance_to_type(model_instance):
        return PoolGroupType(id=model_instance.id,
                             verbose_name=model_instance.verbose_name,
                             description=model_instance.description)


class PoolType(graphene.ObjectType):

    # Pool fields
    master_id = graphene.UUID()
    pool_id = graphene.UUID()
    verbose_name = graphene.String()
    status = StatusGraphene()
    pool_type = graphene.String()
    cluster_id = graphene.UUID()
    node_id = graphene.UUID()
    controller = graphene.Field(ControllerType)
    vm_amount = graphene.Int()

    # StaticPool fields
    static_pool_id = graphene.UUID()

    # AutomatedPool fields
    automated_pool_id = graphene.UUID()
    template_id = graphene.UUID()
    datapool_id = graphene.UUID()
    min_size = graphene.Int()
    max_size = graphene.Int()
    max_vm_amount = graphene.Int()
    increase_step = graphene.Int()
    max_amount_of_create_attempts = graphene.Int()
    initial_size = graphene.Int()
    reserve_size = graphene.Int()
    total_size = graphene.Int()
    vm_name_template = graphene.String()
    os_type = graphene.String()

    users = graphene.List(UserType, entitled=graphene.Boolean())
    assigned_roles = graphene.List(RoleTypeGraphene)
    possible_roles = graphene.List(RoleTypeGraphene)
    assigned_groups = graphene.List(PoolGroupType, limit=graphene.Int(default_value=100),
                                    offset=graphene.Int(default_value=0))
    possible_groups = graphene.List(PoolGroupType)

    keep_vms_on = graphene.Boolean()
    create_thin_clones = graphene.Boolean()
    assigned_connection_types = graphene.List(ConnectionTypesGraphene)
    possible_connection_types = graphene.List(ConnectionTypesGraphene)

    # Затрагивает запрос ресурсов на VeiL ECP.
    template = graphene.Field(VeilShortEntityType)
    node = graphene.Field(VeilShortEntityType)
    cluster = graphene.Field(VeilShortEntityType)
    datapool = graphene.Field(VeilShortEntityType)
    vms = graphene.List(VmType)

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
        vms = await pool.vms
        # TODO: получить список ВМ и статусов
        return [VmType(**vm.__values__) for vm in vms]

    async def resolve_vm_amount(self, _info):
        return await (db.select([db.func.count(Vm.id)]).where(Vm.pool_id == self.pool_id)).gino.scalar()

    async def resolve_template(self, _info):
        pool = await Pool.get(self.pool_id)
        pool_controller = await pool.controller_obj
        template_id = await pool.template_id
        if not template_id:
            return
        veil_domain = pool_controller.veil_client.domain(str(template_id))
        await veil_domain.info()
        # попытка не использовать id
        veil_domain.id = veil_domain.api_object_id
        return veil_domain

    async def resolve_node(self, _info):
        pool = await Pool.get(self.pool_id)
        pool_controller = await pool.controller_obj
        veil_node = pool_controller.veil_client.node(str(pool.node_id))
        await veil_node.info()
        # попытка не использовать id
        veil_node.id = veil_node.api_object_id
        return veil_node

    async def resolve_datapool(self, _info):
        pool = await Pool.get(self.pool_id)
        pool_controller = await pool.controller_obj
        veil_datapool = pool_controller.veil_client.data_pool(str(pool.datapool_id))
        await veil_datapool.info()
        # попытка не использовать id
        veil_datapool.id = veil_datapool.api_object_id
        return veil_datapool

    async def resolve_cluster(self, _info):
        pool = await Pool.get(self.pool_id)
        pool_controller = await pool.controller_obj
        veil_cluster = pool_controller.veil_client.cluster(str(pool.cluster_id))
        await veil_cluster.info()
        # попытка не использовать id
        veil_cluster.id = veil_cluster.api_object_id
        return veil_cluster

    async def resolve_assigned_connection_types(self, _info):
        pool = await Pool.get(self.pool_id)
        return pool.connection_types

    async def resolve_possible_connection_types(self, _info):
        pool = await Pool.get(self.pool_id)
        return await pool.possible_connection_types


def pool_obj_to_type(pool_obj: Pool) -> dict:
    pool_dict = {'pool_id': pool_obj.master_id,
                 'master_id': pool_obj.master_id,
                 'verbose_name': pool_obj.verbose_name,
                 'pool_type': pool_obj.pool_type,
                 'cluster_id': pool_obj.cluster_id,
                 'node_id': pool_obj.node_id,
                 'static_pool_id': pool_obj.master_id,
                 'automated_pool_id': pool_obj.master_id,
                 'template_id': pool_obj.template_id,
                 'datapool_id': pool_obj.datapool_id,
                 'min_size': pool_obj.min_size,
                 'max_size': pool_obj.max_size,
                 'max_vm_amount': pool_obj.max_vm_amount,
                 'increase_step': pool_obj.increase_step,
                 'max_amount_of_create_attempts': pool_obj.max_amount_of_create_attempts,
                 'initial_size': pool_obj.initial_size,
                 'reserve_size': pool_obj.reserve_size,
                 'total_size': pool_obj.total_size,
                 'vm_name_template': pool_obj.vm_name_template,
                 'os_type': pool_obj.os_type,
                 'keep_vms_on': pool_obj.keep_vms_on,
                 'create_thin_clones': pool_obj.create_thin_clones,
                 'controller': pool_obj.controller,
                 'status': pool_obj.status,
                 # 'assigned_connection_types': pool_obj.connection_types
                 }
    return PoolType(**pool_dict)


class PoolQuery(graphene.ObjectType):
    pools = graphene.List(PoolType, status=StatusGraphene(), limit=graphene.Int(default_value=100),
                          offset=graphene.Int(default_value=0),
                          ordering=graphene.String())
    pool = graphene.Field(PoolType, pool_id=graphene.String())

    @staticmethod
    def build_filters(status):
        filters = []
        if status is not None:
            filters.append((Pool.status == status))

        return filters

    @administrator_required
    async def resolve_pools(self, info, limit, offset, status=None, ordering=None, **kwargs):
        filters = PoolQuery.build_filters(status)

        # Сортировка может быть по полю модели Pool, либо по Pool.EXTRA_ORDER_FIELDS
        pools = await Pool.get_pools(limit, offset, filters=filters, ordering=ordering)
        objects = [
            pool_obj_to_type(pool)
            for pool in pools
        ]
        return objects

    @administrator_required
    async def resolve_pool(self, _info, pool_id, **kwargs):
        pool = await Pool.get_pool(pool_id)
        if not pool:
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            raise SimpleError(_('No such pool.'), entity=entity)
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
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            raise SimpleError(_('No such pool.'), entity=entity)

        try:
            pool_type = await pool.pool_type

            # Авто пул
            if pool_type == Pool.PoolTypes.AUTOMATED:
                is_deleted = await execute_delete_pool_task(str(pool.id), full=full, wait_for_result=False)
            else:
                is_deleted = await Pool.delete_pool(pool, creator, full)
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
        cluster_id = graphene.UUID(required=True)
        node_id = graphene.UUID(required=True)
        datapool_id = graphene.UUID(required=True)
        verbose_name = graphene.String(required=True)
        vms = graphene.NonNull(graphene.List(graphene.NonNull(VmInput)))
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene),
                                         default_value=[Pool.PoolConnectionTypes.SPICE.value])
    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, creator, controller_id, cluster_id, node_id, datapool_id, verbose_name, vms,
                     connection_types):
        """Мутация создания Статического пула виртуальных машин.

        1. Проверка переданных vm_ids
        2. Получение дополнительной информации (datapool_id, cluster_id, node_id, controller_address
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
            pool = await StaticPool.soft_create(veil_vm_data=vms,
                                                verbose_name=verbose_name,
                                                cluster_id=cluster_id,
                                                datapool_id=datapool_id,
                                                controller_address=controller.address,
                                                node_id=node_id,
                                                connection_types=connection_types,
                                                creator=creator)
        except Exception as E:  # Возможные исключения: дубликат имени или вм id, сетевой фейл enable_remote_accesses
            # TODO: указать конкретные Exception
            desc = str(E)
            error_msg = _('Failed to create static pool {}.').format(verbose_name)
            await system_logger.debug(desc)
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            raise SimpleError(error_msg, description=desc, entity=entity)
        # Активация удаленного доступа к VM на Veil будет выполнена в момент подключения
        return {
            'pool': PoolType(pool_id=pool.id, verbose_name=verbose_name, vms=vms),
            'ok': True
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
        # pool_controller = await Controller.get(pool.controller)
        # pool_data = await Pool.select('controller', 'node_id').where(Pool.id == pool_id).gino.first()
        # (controller_id, node_id) = pool_data
        # controller_address = await Controller.select('address').where(Controller.id == controller_id).gino.scalar()

        # TODO: есть сомнения в целесообразности этой проверки, ведь если это
        #   недопустимая операция - ее отклонит VeiL.
        # vm checks
        # vm_http_client = await VmHttpClient.create(controller_address, '')
        # all_vms_on_node = await vm_http_client.fetch_vms_list(node_id=node_id)

        # all_vm_ids_on_node = [vmachine['id'] for vmachine in all_vms_on_node]
        used_vm_ids = await Vm.get_all_vms_ids()  # get list of vms which are already in pools

        # await system_logger.debug(_('VM ids: {}').format(vm_ids))

        for vm_id in [vm.id for vm in vms]:
            # check if vm exists and it is on the correct node
            # if str(vm_id) not in all_vm_ids_on_node:
            #     entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            #     raise SimpleError(_('VM {} is at server different from pool server now').format(vm_id), entity=entity)
            # check if vm is free (not in any pool)
            if vm_id in used_vm_ids:
                entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
                raise SimpleError(_('VM {} is already in one of pools').format(vm_id), entity=entity)

        # remote access
        # TODO: использовать нормальный набор данных с verbose_name и id
        # Add VMs to db
        for vm in vms:
            await Vm.create(id=vm.id,
                            template_id=None,
                            pool_id=pool_id,
                            created_by_vdi=False,
                            verbose_name=vm.verbose_name
                            )
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            await system_logger.info(_('Vm {} is added to pool {}').format(vm.verbose_name, pool.verbose_name),
                                     user=creator, entity=entity)

        return {'ok': True}


class RemoveVmsFromStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, pool_id, vm_ids, creator):
        if not vm_ids:
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            raise SimpleError(_("List of VM should not be empty"), entity=entity)

        # vms check
        # get list of vms ids which are in pool_id
        vms_ids_in_pool = await Vm.get_vms_ids_in_pool(pool_id)

        # check if given vm_ids in vms_ids_in_pool
        for vm_id in vm_ids:
            if str(vm_id) not in vms_ids_in_pool:
                entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
                raise SimpleError(_('VM doesn\'t belong to specified pool').format(vm_id), entity=entity)

        # remove vms from db
        await Vm.remove_vms(vm_ids, creator)

        return {
            'ok': True
        }


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
            ok = await StaticPool.soft_update(kwargs['pool_id'], kwargs.get('verbose_name'), kwargs.get('keep_vms_on'),
                                              kwargs.get('connection_types'), creator)
        except UniqueViolationError:
            error_msg = _('Failed to update static pool {}. Name must be unique.').format(kwargs['pool_id'])
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            raise SimpleError(error_msg, user=creator, entity=entity)
        return UpdateStaticPoolMutation(ok=ok)


class ExpandPoolMutation(graphene.Mutation, PoolValidator):
    """Запускает задачу на расширение пула"""
    class Arguments:
        pool_id = graphene.UUID(required=True)

    ok = graphene.Boolean()
    task_id = graphene.UUID()

    @classmethod
    @administrator_required
    async def mutate(cls, _root, _info, creator, pool_id):

        await cls.validate_pool_id(dict(), pool_id)

        task_id = await request_to_execute_pool_task(pool_id, PoolTaskType.EXPANDING_POOL, ignore_reserve_size=True)
        return {
            'ok': True,
            'task_id': task_id,
        }


# --- --- --- --- ---
# Automated (Dynamic) pool mutations
class CreateAutomatedPoolMutation(graphene.Mutation, PoolValidator, ControllerFetcher):
    class Arguments:
        controller_id = graphene.UUID(required=True)
        cluster_id = graphene.UUID(required=True)
        template_id = graphene.UUID(required=True)
        datapool_id = graphene.UUID(required=True)
        node_id = graphene.UUID(required=True)

        verbose_name = graphene.String(required=True)
        # min_size = graphene.Int(default_value=1)
        # max_size = graphene.Int(default_value=200)
        # max_vm_amount = graphene.Int(default_value=1000)
        increase_step = graphene.Int(default_value=3, description="Шаг расширения пула")
        # max_amount_of_create_attempts = graphene.Int(default_value=15)
        initial_size = graphene.Int(default_value=1)
        reserve_size = graphene.Int(default_value=1)
        total_size = graphene.Int(default_value=1)
        vm_name_template = graphene.String(required=True)

        create_thin_clones = graphene.Boolean(default_value=True)
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene),
                                         default_value=[Pool.PoolConnectionTypes.SPICE.value])
        ad_cn_pattern = graphene.String(description="Наименование групп для добавления ВМ в AD")

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, creator, controller_id, cluster_id, template_id, datapool_id, node_id,
                     verbose_name, increase_step,
                     initial_size, reserve_size, total_size, vm_name_template,
                     create_thin_clones,
                     connection_types, ad_cn_pattern: str = None):
        """Мутация создания Автоматического(Динамического) пула виртуальных машин.

        TODO: описать механизм работы"""

        # Проверяем наличие записи
        controller = await cls.fetch_by_id(controller_id)
        # TODO: дооживить валидатор
        await cls.validate(vm_name_template=vm_name_template,
                           verbose_name=verbose_name)
        # --- Создание записей в БД
        try:
            automated_pool = await AutomatedPool.soft_create(creator=creator, verbose_name=verbose_name,
                                                             controller_ip=controller.address, cluster_id=cluster_id,
                                                             node_id=node_id, template_id=template_id,
                                                             datapool_id=datapool_id,
                                                             increase_step=increase_step,
                                                             initial_size=initial_size, reserve_size=reserve_size,
                                                             total_size=total_size,
                                                             vm_name_template=vm_name_template,
                                                             create_thin_clones=create_thin_clones,
                                                             connection_types=connection_types,
                                                             ad_cn_pattern=ad_cn_pattern)
        except Exception as E:  # Возможные исключения: дубликат имени или вм id, сетевой фейл enable_remote_accesses
            desc = str(E)
            error_msg = _('Failed to create automated pool {}.').format(verbose_name)
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            await system_logger.debug(desc)
            raise SimpleError(error_msg, description=desc, user=creator, entity=entity)

        # send command to start pool init task
        await request_to_execute_pool_task(str(automated_pool.id), PoolTaskType.CREATING_POOL)

        # pool creation task successfully started
        pool = await Pool.get_pool(automated_pool.id)
        return CreateAutomatedPoolMutation(
            pool=pool_obj_to_type(pool),
            ok=True)


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
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene))

    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        automated_pool = await AutomatedPool.get(kwargs['pool_id'])
        if automated_pool:
            try:
                await automated_pool.soft_update(verbose_name=kwargs.get('verbose_name'),
                                                 reserve_size=kwargs.get('reserve_size'),
                                                 total_size=kwargs.get('total_size'),
                                                 increase_step=kwargs.get('increase_step'),
                                                 vm_name_template=kwargs.get('vm_name_template'),
                                                 keep_vms_on=kwargs.get('keep_vms_on'),
                                                 create_thin_clones=kwargs.get('create_thin_clones'),
                                                 connection_types=kwargs.get('connection_types'),
                                                 creator=creator
                                                 )
            except UniqueViolationError:
                error_msg = _('Failed to update automated pool {}. Name must be unique.').format(kwargs['verbose_name'])
                entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
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
        if not vm_ids:
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            raise SimpleError(_("List of VM should not be empty"), entity=entity)

        # vms check
        # get list of vms ids which are in pool_id
        vms_ids_in_pool = await Vm.get_vms_ids_in_pool(pool_id)

        # check if given vm_ids in vms_ids_in_pool
        for vm_id in vm_ids:
            if str(vm_id) not in vms_ids_in_pool:
                entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
                raise SimpleError(_('VM doesn\'t belong to specified pool').format(vm_id), entity=entity)

        # remove vms from db
        await Vm.remove_vms(vm_ids, creator, True)

        return {
            'ok': True
        }


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
            return {'ok': False}

        await pool.add_users(users, creator=creator)
        pool_record = await Pool.get_pool(pool.id)
        return PoolUserAddPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


class PoolUserDropPermissionsMutation(graphene.Mutation):

    class Arguments:
        pool_id = graphene.UUID(required=True)
        users = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))
        free_assigned_vms = graphene.Boolean()

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, users, free_assigned_vms=True, creator='system'):
        pool = await Pool.get(pool_id)
        if not pool:
            return PoolUserDropPermissionsMutation(ok=False)

        async with db.transaction():
            await pool.remove_users(creator, users)
            if free_assigned_vms:
                await pool.free_assigned_vms(users)

        pool_record = await Pool.get_pool(pool.id)
        return PoolUserDropPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


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
            return {'ok': False}

        await pool.add_groups(creator, groups)

        pool_record = await Pool.get_pool(pool.id)
        return PoolGroupAddPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


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
            return {'ok': False}

        await pool.remove_groups(creator, groups)

        pool_record = await Pool.get_pool(pool.id)
        return PoolGroupDropPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


class PoolRoleAddPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, roles, creator):
        pool = await Pool.get(pool_id)
        if not pool:
            return {'ok': False}

        await pool.add_roles(roles, creator)

        pool_record = await Pool.get_pool(pool.id)
        return PoolRoleAddPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


class PoolRoleDropPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, roles, creator):
        pool = await Pool.get(pool_id)
        if not pool:
            return {'ok': False}

        await pool.remove_roles(creator, roles)

        pool_record = await Pool.get_pool(pool.id)
        return PoolRoleAddPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


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
            raise SimpleError(_('There is no VM {}').format(vm_id))

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
                raise SimpleError(_('User does not have the right to use pool, which has VM.'))

            # another vm in the pool may have this user as owner. Remove assignment
            await pool.free_user_vms(user_id)

        # Сейчас за VM может быть только 1 пользователь. Освобождаем от других.
        await vm.remove_users(creator, users_list=None)
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
            await vm.remove_users(creator, users_list=None)
            return FreeVmFromUser(ok=True)
        return FreeVmFromUser(ok=False)


class PrepareVm(graphene.Mutation):
    class Arguments:
        vm_id = graphene.ID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, **kwargs):
        vm = await Vm.get(vm_id)
        if vm:
            active_directory_object = None
            ad_cn_pattern = None

            pool = await Pool.get(vm.pool_id)

            pool_type = await pool.pool_type
            if pool_type == Pool.PoolTypes.AUTOMATED:
                auto_pool = await AutomatedPool.get(pool.id)
                active_directory_object = await AuthenticationDirectory.query.where(
                    AuthenticationDirectory.status == Status.ACTIVE).gino.first()
                ad_cn_pattern = auto_pool.ad_cn_pattern
            asyncio.ensure_future(vm.prepare_with_timeout(active_directory_object, ad_cn_pattern))
            # future = asyncio.ensure_future(vm.prepare_with_timeout(active_directory_object, ad_cn_pattern))
            # future.add_done_callback(lambda f: print('FINISH'))  # делаем что-то после окончания
            # выполняем любой код ниже
            return PrepareVm(ok=True)
        return PrepareVm(ok=False)


class VmStart(graphene.Mutation):
    class Arguments:
        vm_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, vm_id, creator, **kwargs):
        vm = await Vm.get(vm_id)
        if vm:
            domain_entity = await vm.vm_client
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
            await domain_entity.info()
            asyncio.ensure_future(vm.reboot(creator=creator, force=force))
            return VmReboot(ok=True)
        return VmReboot(ok=False)


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
    addPoolRole = PoolRoleAddPermissionsMutation.Field()
    removePoolRole = PoolRoleDropPermissionsMutation.Field()

    # Vm mutations
    assignVmToUser = AssignVmToUser.Field()
    freeVmFromUser = FreeVmFromUser.Field()
    prepareVm = PrepareVm.Field()
    startVm = VmStart.Field()
    shutdownVm = VmShutdown.Field()
    rebootVm = VmReboot.Field()


pool_schema = graphene.Schema(query=PoolQuery,
                              mutation=PoolMutations,
                              auto_camelcase=False)
