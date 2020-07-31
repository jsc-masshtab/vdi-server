# -*- coding: utf-8 -*-
import re

import graphene
# from tornado.httpclient import HTTPClientError  # TODO: точно это нужно тут?
from asyncpg.exceptions import UniqueViolationError

from common.database import db
from common.veil.veil_gino import RoleTypeGraphene, Role, StatusGraphene, Status
from common.veil.veil_validators import MutationValidation
from common.veil.veil_errors import SimpleError, HttpError, ValidationError
# from common.utils import make_graphene_type
from common.veil.veil_decorators import administrator_required
from common.veil.veil_graphene import VmState
from common.models.auth import User
from web_app.auth.user_schema import UserType

# from vm.schema import VmType, VmQuery, TemplateType
from common.models.vm import Vm
# from vm.veil_client import VmHttpClient

from web_app.controller.schema import ControllerType
from common.models.controller import Controller

# from controller_resources.veil_client import ResourcesHttpClient
# from controller_resources.schema import ClusterType, NodeType, DatapoolType

from common.models.pool import AutomatedPool, StaticPool, Pool

from common.languages import lang_init
from common.log.journal import system_logger

from common.veil.veil_redis import request_to_execute_pool_task, PoolTaskType


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


class VmType(graphene.ObjectType):
    verbose_name = graphene.String()
    id = graphene.String()
    # veil_info = graphene.String()
    # veil_info_json = graphene.String()
    # template = graphene.Field(TemplateType)
    user = graphene.Field(UserType)
    state = graphene.Field(VmState)
    status = graphene.String()
    controller = graphene.Field(ControllerType)


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
    async def validate_controller_ip(obj_dict, value):
        if not value:
            return
        ip_re = re.compile(
            r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
        )
        ip = re.fullmatch(ip_re, value)
        if ip:
            return value
        raise ValidationError(_('ip-address probably invalid.'))

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

        name_re = re.compile('^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$')
        template_name = re.match(name_re, value)
        if template_name:
            return value
        raise ValidationError(_('Template name of VM must contain only characters, digits, _, -'))

    @staticmethod
    async def validate_initial_size(obj_dict, value):
        if not value:
            return
        if value < obj_dict['min_size'] or value > obj_dict['max_size']:
            raise ValidationError(
                _('Initial number of VM must be in {}-{} interval').format(obj_dict['min_size'], obj_dict['max_size']))
        return value

    @staticmethod
    async def validate_reserve_size(obj_dict, value):
        if not value:
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
        if not value:
            return

        pool_id = obj_dict.get('pool_id')
        if pool_id:
            pool_obj = await Pool.get_pool(pool_id)
            initial_size = obj_dict['initial_size'] if obj_dict.get('initial_size') else pool_obj.initial_size
            min_size = obj_dict['min_size'] if obj_dict.get('min_size') else pool_obj.min_size
            max_vm_amount = obj_dict['max_vm_amount'] if obj_dict.get('max_vm_amount') else pool_obj.max_vm_amount
        else:
            initial_size = obj_dict['initial_size']
            min_size = obj_dict['min_size']
            max_vm_amount = obj_dict['max_vm_amount']

        if value < initial_size:
            raise ValidationError(_('Maximal number of created VM should be less than initial number of VM'))
        if value < min_size or value > max_vm_amount:
            raise ValidationError(_('Maximal number of created VM must be in [{} {}] interval').
                                  format(min_size, max_vm_amount))
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
    # vms = graphene.List(VmType)
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
    min_free_vms_amount = graphene.Int()
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

    # node = graphene.Field(NodeType)
    # cluster = graphene.Field(ClusterType)
    # datapool = graphene.Field(DatapoolType)
    # template = graphene.Field(TemplateType)

    keep_vms_on = graphene.Boolean()
    create_thin_clones = graphene.Boolean()
    assigned_connection_types = graphene.List(ConnectionTypesGraphene)
    possible_connection_types = graphene.List(ConnectionTypesGraphene)

    async def resolve_controller(self, info):
        controller_obj = await Controller.get(self.controller)
        return ControllerType(**controller_obj.__values__)

    async def resolve_assigned_roles(self, info):
        pool = await Pool.get(self.pool_id)
        roles = await pool.roles
        return [role_type.role for role_type in roles]

    async def resolve_possible_roles(self, info):
        pool = await Pool.get(self.pool_id)
        assigned_roles = await pool.roles
        all_roles = [role_type for role_type in Role]
        return [role for role in all_roles if role.value not in assigned_roles]

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
        await self._build_vms_list()
        return self.vms

    async def resolve_vm_amount(self, _info):
        return await (db.select([db.func.count(Vm.id)]).where(Vm.pool_id == self.pool_id)).gino.scalar()

    # async def resolve_node(self, _info):
    #     controller_address = await Pool.get_controller_ip(self.pool_id)
    #     resources_http_client = await ResourcesHttpClient.create(controller_address)
    #     node_id = await Pool.select('node_id').where(Pool.id == self.pool_id).gino.scalar()
    #
    #     node_data = await resources_http_client.fetch_node(node_id)
    #     node_type = make_graphene_type(NodeType, node_data)
    #     node_type.controller = ControllerType(address=controller_address)
    #     return node_type

    # async def resolve_cluster(self, _info):
    #     controller_address = await Pool.get_controller_ip(self.pool_id)
    #     resources_http_client = await ResourcesHttpClient.create(controller_address)
    #     cluster_id = await Pool.select('cluster_id').where(Pool.id == self.pool_id).gino.scalar()
    #
    #     cluster_data = await resources_http_client.fetch_cluster(cluster_id)
    #     cluster_type = make_graphene_type(ClusterType, cluster_data)
    #     cluster_type.controller = ControllerType(address=controller_address)
    #     return cluster_type

    # async def resolve_datapool(self, _info):
    #     pool = await Pool.get(self.pool_id)
    #     controller_address = await Pool.get_controller_ip(self.pool_id)
    #     resources_http_client = await ResourcesHttpClient.create(controller_address)
    #     datapool_id = pool.datapool_id
    #     try:
    #         datapool_data = await resources_http_client.fetch_datapool(datapool_id)
    #         datapool_type = make_graphene_type(DatapoolType, datapool_data)
    #         datapool_type.controller = ControllerType(address=controller_address)
    #         return datapool_type
    #     except (HTTPClientError, HttpError):
    #         return None

    # async def resolve_template(self, _info):
    #     controller_address = await Pool.get_controller_ip(self.pool_id)
    #     template_id = await AutomatedPool.select('template_id').where(
    #         AutomatedPool.id == self.pool_id).gino.scalar()
    #     vm_http_client = await VmHttpClient.create(controller_address, template_id)
    #
    #     try:
    #         veil_info = await vm_http_client.info()
    #         return VmQuery.veil_template_data_to_graphene_type(veil_info, controller_address)
    #     except (HTTPClientError, HttpError):
    #         # либо шаблон изчес с контроллера, либо попытка получить шаблон для статического пула
    #         return None

    # async def _build_vms_list(self):
    #     if not self.vms:
    #         self.vms = []
    #
    #         controller_address = await Pool.get_controller_ip(self.pool_id)
    #         vm_http_client = await VmHttpClient.create(controller_address, '')
    #         vm_veil_data_list = await vm_http_client.fetch_vms_list()
    #
    #         db_vms_data = await Vm.select("id").where((Vm.pool_id == self.pool_id)).gino.all()
    #
    #         for (vm_id,) in db_vms_data:
    #             try:
    #                 remote_vm_data = next(data for data in vm_veil_data_list if data['id'] == str(vm_id))
    #                 vm_type = VmQuery.veil_vm_data_to_graphene_type(remote_vm_data, controller_address)
    #             except StopIteration:
    #                 vm_type = VmType(id=vm_id, controller=ControllerType(address=controller_address))
    #                 vm_type.veil_info = None
    #
    #             self.vms.append(vm_type)

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
            raise SimpleError(_('No such pool.'))
        return pool_obj_to_type(pool)


# --- --- --- --- ---
# Pool mutations
class DeletePoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        pool_id = graphene.UUID()
        full = graphene.Boolean(required=False)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, info, pool_id, creator, full=False):

        # Нет запуска валидации, т.к. нужна сущность пула далее - нет смысла запускать запрос 2жды.
        # print('pool_id', pool_id)
        pool = await Pool.get(pool_id)
        if not pool:
            raise SimpleError(_('No such pool.'))

        try:
            pool_type = await pool.pool_type

            # Авто пул
            if pool_type == Pool.PoolTypes.AUTOMATED:
                is_deleted = await AutomatedPool.delete_pool(pool, full)
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
        # if not vm_ids:
        #     # graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))
        #     raise SimpleError('VM ids is empty.')

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
            # vms = [VmType(id=vm_id) for vm_id in vm_ids]
        except Exception as E:  # Возможные исключения: дубликат имени или вм id, сетевой фейл enable_remote_accesses
            # TODO: указать конкретные Exception
            desc = str(E)
            error_msg = _('Failed to create static pool {}.').format(verbose_name)
            await system_logger.debug(desc)
            raise SimpleError(error_msg, description=desc)
        # --- Активация удаленного доступа к VM на Veil
        try:
            await Vm.enable_remote_accesses(controller.address, vms)
        except HttpError:
            msg = _('Fail with remote access enable.')
            await system_logger.warning(msg)
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
        pool_controller = await pool.controller
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
            #     raise SimpleError(_('VM {} is at server different from pool server now').format(vm_id))
            # check if vm is free (not in any pool)
            if vm_id in used_vm_ids:
                raise SimpleError(_('VM {} is already in one of pools').format(vm_id))

        # remote access
        await Vm.enable_remote_accesses(pool_controller.address, vms)

        # await system_logger.debug(_('All VMs on node: {}').format(all_vms_on_node))

        # TODO: использовать нормальный набор данных с verbose_name и id
        # Add VMs to db
        for vm in vms:
            await Vm.create(id=vm.id,
                            template_id=None,
                            pool_id=pool_id,
                            created_by_vdi=False,
                            verbose_name=vm.verbose_name
                            )
            await system_logger.info(_('Vm {} is added to pool {}').format(vm.verbose_name, pool.verbose_name),
                                     user=creator)

        return {'ok': True}


class RemoveVmsFromStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.ID, required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, pool_id, vm_ids, creator):
        if not vm_ids:
            raise SimpleError(_("List of VM should not be empty"))

        # vms check
        # get list of vms ids which are in pool_id
        vms_ids_in_pool = await Vm.get_vms_ids_in_pool(pool_id)

        # check if given vm_ids in vms_ids_in_pool
        for vm_id in vm_ids:
            if vm_id not in vms_ids_in_pool:
                raise SimpleError(_('VM doesn\'t belong to specified pool').format(vm_id))

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
            raise SimpleError(error_msg, user=creator)
        return UpdateStaticPoolMutation(ok=ok)


# --- --- --- --- ---
# Automated (Dynamic) pool mutations
class CreateAutomatedPoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        verbose_name = graphene.String(required=True)
        controller_ip = graphene.String(required=True)
        cluster_id = graphene.UUID(required=True)
        template_id = graphene.UUID(required=True)
        datapool_id = graphene.UUID(required=True)
        node_id = graphene.UUID(required=True)

        min_size = graphene.Int(default_value=1)
        max_size = graphene.Int(default_value=200)
        max_vm_amount = graphene.Int(default_value=1000)
        increase_step = graphene.Int(default_value=3)
        min_free_vms_amount = graphene.Int(default_value=5)
        max_amount_of_create_attempts = graphene.Int(default_value=15)
        initial_size = graphene.Int(default_value=1)
        reserve_size = graphene.Int(default_value=1)
        total_size = graphene.Int(default_value=1)
        vm_name_template = graphene.String(default_value='')

        create_thin_clones = graphene.Boolean(default_value=True)
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene),
                                         default_value=[Pool.PoolConnectionTypes.SPICE.value])

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        try:
            automated_pool = await AutomatedPool.soft_create(**kwargs)
        except UniqueViolationError:
            error_msg = _('Failed to create automated pool {}. Name must be unique.').format(kwargs['verbose_name'])
            # await system_logger.error(error_msg, user=creator)
            raise SimpleError(error_msg, user=creator)

        # send command to start pool init task
        await request_to_execute_pool_task(str(automated_pool.id), PoolTaskType.CREATING.name)

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
        vm_name_template = graphene.String()
        keep_vms_on = graphene.Boolean()
        create_thin_clones = graphene.Boolean()
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene))

    ok = graphene.Boolean()

    @staticmethod
    async def validate_total_size(obj_dict, value):
        if not value:
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
        if total_size and value <= total_size:
            raise ValidationError(_('Maximal number of created VM can not be reduced.'))
        return value

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
                                                 vm_name_template=kwargs.get('vm_name_template'),
                                                 keep_vms_on=kwargs.get('keep_vms_on'),
                                                 create_thin_clones=kwargs.get('create_thin_clones'),
                                                 connection_types=kwargs.get('connection_types'),
                                                 creator=creator
                                                 )
            except UniqueViolationError:
                error_msg = _('Failed to update automated pool {}. Name must be unique.').format(kwargs['verbose_name'])
                # await system_logger.error(error_msg, user=creator)
                raise SimpleError(error_msg, user=creator)
            else:
                return UpdateAutomatedPoolMutation(ok=True)
        return UpdateAutomatedPoolMutation(ok=False)


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


# --- --- --- --- ---
# Schema concatenation
class PoolMutations(graphene.ObjectType):
    addDynamicPool = CreateAutomatedPoolMutation.Field()
    addStaticPool = CreateStaticPoolMutation.Field()
    addVmsToStaticPool = AddVmsToStaticPoolMutation.Field()
    removeVmsFromStaticPool = RemoveVmsFromStaticPoolMutation.Field()
    removePool = DeletePoolMutation.Field()
    updateDynamicPool = UpdateAutomatedPoolMutation.Field()
    updateStaticPool = UpdateStaticPoolMutation.Field()

    entitleUsersToPool = PoolUserAddPermissionsMutation.Field()
    removeUserEntitlementsFromPool = PoolUserDropPermissionsMutation.Field()
    addPoolGroup = PoolGroupAddPermissionsMutation.Field()
    removePoolGroup = PoolGroupDropPermissionsMutation.Field()
    addPoolRole = PoolRoleAddPermissionsMutation.Field()
    removePoolRole = PoolRoleDropPermissionsMutation.Field()

    # Vm mutations
    assignVmToUser = AssignVmToUser.Field()
    freeVmFromUser = FreeVmFromUser.Field()


pool_schema = graphene.Schema(query=PoolQuery,
                              mutation=PoolMutations,
                              auto_camelcase=False)
