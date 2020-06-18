# -*- coding: utf-8 -*-
import re
import uuid
import json

import graphene
from tornado.httpclient import HTTPClientError  # TODO: точно это нужно тут?
from asyncpg.exceptions import UniqueViolationError

from database import StatusGraphene, db, RoleTypeGraphene, Role
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, HttpError, ValidationError
from common.utils import make_graphene_type
from common.veil_decorators import administrator_required

from auth.user_schema import UserType

from vm.schema import VmType, VmQuery, TemplateType
from vm.models import Vm
from vm.veil_client import VmHttpClient

from controller.schema import ControllerType
from controller.models import Controller

from controller_resources.veil_client import ResourcesHttpClient
from controller_resources.schema import ClusterType, NodeType, DatapoolType

from pool.models import AutomatedPool, StaticPool, Pool

from languages import lang_init
from journal.journal import Log as log

from redis_broker import request_to_execute_pool_task, PoolTaskType, a_redis_wait_for_message, INTERNAL_EVENTS_CHANNEL


_ = lang_init()

# TODO: отсутствует валидация входящих ресурсов вроде node_uid, cluster_uid и т.п. Ранее шла речь,
#  о том, что мы будем кешированно хранить какие-то ресурсы полученные от ECP Veil. Возможно стоит
#  обращаться к этому хранилищу для проверки корректности присланных ресурсов. Аналогичный принцип
#  стоит применить и к статическим пулам (вместо похода на вейл для проверки присланных параметров).

ConnectionTypesGraphene = graphene.Enum.from_enum(Pool.PoolConnectionTypes)


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
    vms = graphene.List(VmType)
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
    assigned_groups = graphene.List(PoolGroupType)
    possible_groups = graphene.List(PoolGroupType)

    node = graphene.Field(NodeType)
    cluster = graphene.Field(ClusterType)
    datapool = graphene.Field(DatapoolType)
    template = graphene.Field(TemplateType)

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

    async def resolve_assigned_groups(self, info):
        pool = await Pool.get(self.pool_id)
        return await pool.assigned_groups

    async def resolve_possible_groups(self, _info):
        pool = await Pool.get(self.pool_id)
        return await pool.possible_groups

    async def resolve_users(self, _info, entitled=True):
        pool = await Pool.get(self.pool_id)
        return await pool.assigned_users if entitled else await pool.possible_users

    async def resolve_vms(self, _info):
        await self._build_vms_list()
        return self.vms

    async def resolve_vm_amount(self, _info):
        return await (db.select([db.func.count(Vm.id)]).where(Vm.pool_id == self.pool_id)).gino.scalar()

    async def resolve_node(self, _info):
        controller_address = await Pool.get_controller_ip(self.pool_id)
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        node_id = await Pool.select('node_id').where(Pool.id == self.pool_id).gino.scalar()

        node_data = await resources_http_client.fetch_node(node_id)
        node_type = make_graphene_type(NodeType, node_data)
        node_type.controller = ControllerType(address=controller_address)
        return node_type

    async def resolve_cluster(self, _info):
        controller_address = await Pool.get_controller_ip(self.pool_id)
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        cluster_id = await Pool.select('cluster_id').where(Pool.id == self.pool_id).gino.scalar()

        cluster_data = await resources_http_client.fetch_cluster(cluster_id)
        cluster_type = make_graphene_type(ClusterType, cluster_data)
        cluster_type.controller = ControllerType(address=controller_address)
        return cluster_type

    async def resolve_datapool(self, _info):
        pool = await Pool.get(self.pool_id)
        controller_address = await Pool.get_controller_ip(self.pool_id)
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        datapool_id = pool.datapool_id
        try:
            datapool_data = await resources_http_client.fetch_datapool(datapool_id)
            datapool_type = make_graphene_type(DatapoolType, datapool_data)
            datapool_type.controller = ControllerType(address=controller_address)
            return datapool_type
        except (HTTPClientError, HttpError):
            return None

    async def resolve_template(self, _info):
        controller_address = await Pool.get_controller_ip(self.pool_id)
        template_id = await AutomatedPool.select('template_id').where(
            AutomatedPool.id == self.pool_id).gino.scalar()
        vm_http_client = await VmHttpClient.create(controller_address, template_id)

        try:
            veil_info = await vm_http_client.info()
            return VmQuery.veil_template_data_to_graphene_type(veil_info, controller_address)
        except (HTTPClientError, HttpError):
            # либо шаблон изчес с контроллера, либо попытка получить шаблон для статического пула
            return None

    async def _build_vms_list(self):
        if not self.vms:
            self.vms = []

            controller_address = await Pool.get_controller_ip(self.pool_id)
            vm_http_client = await VmHttpClient.create(controller_address, '')
            vm_veil_data_list = await vm_http_client.fetch_vms_list()

            db_vms_data = await Vm.select("id").where((Vm.pool_id == self.pool_id)).gino.all()

            for (vm_id,) in db_vms_data:
                try:
                    remote_vm_data = next(data for data in vm_veil_data_list if data['id'] == str(vm_id))
                    vm_type = VmQuery.veil_vm_data_to_graphene_type(remote_vm_data, controller_address)
                except StopIteration:
                    vm_type = VmType(id=vm_id, controller=ControllerType(address=controller_address))
                    vm_type.veil_info = None

                self.vms.append(vm_type)

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
                 'min_free_vms_amount': pool_obj.min_free_vms_amount,
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

    pools = graphene.List(PoolType, ordering=graphene.String())
    pool = graphene.Field(PoolType, pool_id=graphene.String())

    @administrator_required
    async def resolve_pools(self, info, ordering=None):
        # Сортировка может быть по полю модели Pool, либо по Pool.EXTRA_ORDER_FIELDS
        pools = await Pool.get_pools(ordering=ordering)
        objects = [
            pool_obj_to_type(pool)
            for pool in pools
        ]
        return objects

    @administrator_required
    async def resolve_pool(self, _info, pool_id):
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
    async def mutate(self, info, pool_id, full=False):

        def _check_if_pool_deleted(redis_message):

            try:
                redis_message_data = redis_message['data'].decode()
                redis_message_data_dict = json.loads(redis_message_data)

                if str(pool_id) == redis_message_data_dict['pool_id'] and redis_message_data_dict['event'] == 'pool_deleted':
                    return redis_message_data_dict['is_successful']
            except Exception as ex:  # Нас интересует лишь прошла ли проверка
                log.debug('__check_if_pool_deleted ' + str(ex))

            return False

        # Нет запуска валидации, т.к. нужна сущность пула далее - нет смысла запускать запрос 2жды.
        pool = await Pool.get(pool_id)
        if not pool:
            raise SimpleError(_('No such pool.'))

        try:
            pool_type = await pool.pool_type

            # Авто пул
            if pool_type == Pool.PoolTypes.AUTOMATED:
                request_to_execute_pool_task(str(pool_id), PoolTaskType.DELETING.name, deletion_full=full)

                # wait for task result to simulate previous behavior
                is_deleted = await a_redis_wait_for_message(INTERNAL_EVENTS_CHANNEL, _check_if_pool_deleted, timeout=20)
                print('is pool deleted ', is_deleted)
            else:
                is_deleted = await Pool.delete_pool(pool, full)
            return DeletePoolMutation(ok=is_deleted)
        except Exception as e:
            raise e


# --- --- --- --- ---
# Static pool mutations
class CreateStaticPoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        verbose_name = graphene.String(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)
        connection_types = graphene.List(graphene.NonNull(ConnectionTypesGraphene),
                                         default_value=[Pool.PoolConnectionTypes.SPICE.value])
    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    @administrator_required
    async def mutate(cls, root, info, **kwargs):
        """Мутация создания Статического пула виртуальных машин.

        1. Проверка переданных vm_ids
        2. Получение дополнительной информации (datapool_id, cluster_id, node_id, controller_address
        3. Создание Pool
        4. Создание StaticPool
        5. Создание не удаляемых VM в локальной таблице VM
        6. Разрешение удаленного доступа к VM на veil
        7. Активация Pool
        """

        await cls.validate_agruments(**kwargs)
        vm_ids = kwargs['vm_ids']
        verbose_name = kwargs['verbose_name']
        connection_types = kwargs['connection_types']

        # TODO: validate_arguments срабатывает позже чем нужно
        if not vm_ids:
            raise SimpleError('VM ids is empty.')

        # --- Получение дополнительной информации
        log.debug(_('StaticPool: Get additional info from Veil'))
        veil_vm_data_list = await StaticPool.fetch_veil_vm_data(vm_ids)

        first_vm_id = veil_vm_data_list[0]['id']
        first_vm_node_id = veil_vm_data_list[0]['node']['id']
        first_vm_controller_address = veil_vm_data_list[0]['controller_address']

        if not StaticPool.vms_on_same_node(node_id=first_vm_node_id, veil_vm_data=veil_vm_data_list):
            raise SimpleError(_("All of VM must be at one server"))

        log.debug(_('StaticPool: Determine cluster'))
        resources_http_client = await ResourcesHttpClient.create(first_vm_controller_address)
        node_data = await resources_http_client.fetch_node(first_vm_node_id)
        cluster_id = node_data['cluster']

        vm_http_client = await VmHttpClient.create(first_vm_controller_address, first_vm_id)
        disks_list = await vm_http_client.fetch_vdisks_list()
        print('disks_list', disks_list)
        if len(disks_list) < 1:
            raise SimpleError(_('VM has no disks.'))
        datapool_id = disks_list[0]['datapool']['id']

        # --- Создание записей в БД
        try:
            pool = await StaticPool.soft_create(veil_vm_data=veil_vm_data_list, verbose_name=verbose_name,
                                                cluster_id=cluster_id, datapool_id=datapool_id,
                                                controller_address=first_vm_controller_address,
                                                node_id=first_vm_node_id, connection_types=connection_types)
            vms = [VmType(id=vm_id) for vm_id in vm_ids]
        except Exception as E:  # Возможные исключения: дубликат имени или вм id, сетевой фейл enable_remote_accesses
            # TODO: указать конкретные Exception
            desc = str(E)
            error_msg = _('Failed to create static pool {}.').format(verbose_name)
            log.debug(desc)
            raise SimpleError(error_msg, description=desc)
        # --- Активация удаленного доступа к VM на Veil
        try:
            await Vm.enable_remote_accesses(first_vm_controller_address, vm_ids)
        except HttpError:
            msg = _('Fail with remote access enable.')
            await log.warning(msg)
        return {
            'pool': PoolType(pool_id=pool.id, verbose_name=verbose_name, vms=vms),
            'ok': True
        }


class AddVmsToStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise SimpleError(_("List of VM should not be empty"))

        pool_data = await Pool.select('controller', 'node_id').where(Pool.id == pool_id).gino.first()
        (controller_id, node_id) = pool_data
        controller_address = await Controller.select('address').where(Controller.id == controller_id).gino.scalar()

        # vm checks
        vm_http_client = await VmHttpClient.create(controller_address, '')
        all_vms_on_node = await vm_http_client.fetch_vms_list(node_id=node_id)

        all_vm_ids_on_node = [vmachine['id'] for vmachine in all_vms_on_node]
        used_vm_ids = await Vm.get_all_vms_ids()  # get list of vms which are already in pools

        log.debug(_('VM ids: {}').format(vm_ids))

        for vm_id in vm_ids:
            # check if vm exists and it is on the correct node
            if str(vm_id) not in all_vm_ids_on_node:
                raise SimpleError(_('VM {} is at server different from pool server now').format(vm_id))
            # check if vm is free (not in any pool)
            if vm_id in used_vm_ids:
                raise SimpleError(_('VM {} is already in one of pools').format(vm_id))

        # remote access
        await Vm.enable_remote_accesses(controller_address, vm_ids)

        log.debug(_('All VMs on node: {}').format(all_vms_on_node))

        # Add VMs to db
        for vm_info in all_vms_on_node:
            if uuid.UUID(vm_info['id']) in vm_ids:
                await Vm.create(id=vm_info['id'],
                                template_id=None,
                                pool_id=pool_id,
                                created_by_vdi=False,
                                verbose_name=vm_info['verbose_name'])
                name = await Pool.get(pool_id)
                await log.info(_('Vm {} is added to pool {}').format(vm_info['verbose_name'], name.verbose_name))

        return {
            'ok': True
        }


class RemoveVmsFromStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.ID, required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, pool_id, vm_ids):
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
        await Vm.remove_vms(vm_ids)

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
    async def mutate(cls, _root, _info, **kwargs):
        await cls.validate_agruments(**kwargs)
        try:
            ok = await StaticPool.soft_update(kwargs['pool_id'], kwargs.get('verbose_name'), kwargs.get('keep_vms_on'),
                                              kwargs.get('connection_types'))
        except UniqueViolationError:
            error_msg = _('Failed to update static pool {}. Name must be unique.').format(kwargs['pool_id'])
            raise SimpleError(error_msg)
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
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        try:
            automated_pool = await AutomatedPool.soft_create(**kwargs)
        except UniqueViolationError:
            error_msg = _('Failed to create automated pool {}. Name must be unique.').format(kwargs['verbose_name'])
            await log.error(error_msg)
            raise SimpleError(error_msg)

        # send command to start pool init task
        request_to_execute_pool_task(str(automated_pool.id), PoolTaskType.CREATING.name)

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
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        automated_pool = await AutomatedPool.get(kwargs['pool_id'])
        if automated_pool:
            try:
                await automated_pool.soft_update(verbose_name=kwargs.get('verbose_name'),
                                                 reserve_size=kwargs.get('reserve_size'),
                                                 total_size=kwargs.get('total_size'),
                                                 vm_name_template=kwargs.get('vm_name_template'),
                                                 keep_vms_on=kwargs.get('keep_vms_on'),
                                                 create_thin_clones=kwargs.get('create_thin_clones'),
                                                 connection_types=kwargs.get('connection_types'))
            except UniqueViolationError:
                error_msg = _('Failed to update automated pool {}. Name must be unique.').format(kwargs['verbose_name'])
                await log.error(error_msg)
                raise SimpleError(error_msg)
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
    async def mutate(self, _info, pool_id, users):
        pool = await Pool.get(pool_id)
        if not pool:
            return {'ok': False}

        await pool.add_users(users)
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
    async def mutate(self, _info, pool_id, users, free_assigned_vms=True):
        pool = await Pool.get(pool_id)
        if not pool:
            return PoolUserDropPermissionsMutation(ok=False)

        async with db.transaction():
            await pool.remove_users(users)
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
    async def mutate(self, _info, pool_id, groups):
        pool = await Pool.get(pool_id)
        if not pool:
            return {'ok': False}

        await pool.add_groups(groups)

        pool_record = await Pool.get_pool(pool.id)
        return PoolGroupAddPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


class PoolGroupDropPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        groups = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, groups):
        pool = await Pool.get(pool_id)
        if not pool:
            return {'ok': False}

        await pool.remove_groups(groups)

        pool_record = await Pool.get_pool(pool.id)
        return PoolGroupDropPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


class PoolRoleAddPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, roles):
        pool = await Pool.get(pool_id)
        if not pool:
            return {'ok': False}

        await pool.add_roles(roles)

        pool_record = await Pool.get_pool(pool.id)
        return PoolRoleAddPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


class PoolRoleDropPermissionsMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    ok = graphene.Boolean()
    pool = graphene.Field(PoolType)

    @administrator_required
    async def mutate(self, _info, pool_id, roles):
        pool = await Pool.get(pool_id)
        if not pool:
            return {'ok': False}

        await pool.remove_roles(roles)

        pool_record = await Pool.get_pool(pool.id)
        return PoolRoleAddPermissionsMutation(ok=True, pool=pool_obj_to_type(pool_record))


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


pool_schema = graphene.Schema(query=PoolQuery,
                              mutation=PoolMutations,
                              auto_camelcase=False)
