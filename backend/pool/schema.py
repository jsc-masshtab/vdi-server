# -*- coding: utf-8 -*-
import re
import asyncio
import logging

import graphene
from tornado.httpclient import HTTPClientError  # TODO: точно это нужно тут?
from asyncpg.exceptions import UniqueViolationError

from database import StatusGraphene, db
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, HttpError, ValidationError
from common.utils import make_graphene_type
from common.veil_decorators import superuser_required

from user.schema import UserType
from user.models import User
from event.models import Event

from vm.schema import VmType, VmQuery, TemplateType
from vm.models import Vm
from vm.veil_client import VmHttpClient

from controller.schema import ControllerType
from controller.models import Controller

from controller_resources.veil_client import ResourcesHttpClient
from controller_resources.schema import ClusterType, NodeType, DatapoolType

from pool.models import AutomatedPool, StaticPool, Pool, PoolUsers
from pool.pool_task_manager import pool_task_manager


application_log = logging.getLogger('tornado.application')


# TODO: отсутствует валидация входящих ресурсов вроде node_uid, cluster_uid и т.п. Ранее шла речь,
#  о том, что мы будем кешированно хранить какие-то ресурсы полученные от ECP Veil. Возможно стоит
#  обращаться к этому хранилищу для проверки корректности присланных ресурсов. Аналогичный принцип
#  стоит применить и к статическим пулам (вместо похода на вейл для проверки присланных параметров).


class PoolValidator(MutationValidation):
    """Валидатор для сущности Pool"""

    @staticmethod
    async def validate_pool_id(obj_dict, value):
        if not value:
            return
        pool = await Pool.get_pool(value)
        if pool:
            return value
        raise ValidationError('No such pool.')

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
        raise ValidationError('ip-address probably invalid.')

    @staticmethod
    async def validate_verbose_name(obj_dict, value):
        if not value:
            return
        name_re = re.compile('^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$')
        template_name = re.match(name_re, value)
        if template_name:
            return value
        raise ValidationError('Имя пула должно содержать только буквы, цифры, _, -')

    @staticmethod
    async def validate_vm_name_template(obj_dict, value):
        if not value:
            return

        name_re = re.compile('^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$')
        template_name = re.match(name_re, value)
        if template_name:
            return value
        raise ValidationError('Шаблонное имя вм должно содержать только буквы, цифры, _, -')

    @staticmethod
    async def validate_initial_size(obj_dict, value):
        if not value:
            return
        if value < obj_dict['min_size'] or value > obj_dict['max_size']:
            raise ValidationError(
                'Начальное количество ВМ должно быть в интервале {}-{}'.format(obj_dict['min_size'],
                                                                               obj_dict['max_size']))
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
            raise ValidationError('Количество создаваемых ВМ должно быть в интервале {}-{}'.
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
            raise ValidationError('Максимальное количество создаваемых ВМ не может быть меньше '
                                  'начального количества ВМ')
        if value < min_size or value > max_vm_amount:
            raise ValidationError('Максимальное количество создаваемых ВМ должно быть в интервале [{} {}]'.
                                  format(min_size, max_vm_amount))
        return value


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
    max_amount_of_create_attempts = graphene.Int()
    initial_size = graphene.Int()
    reserve_size = graphene.Int()
    total_size = graphene.Int()
    vm_name_template = graphene.String()
    os_type = graphene.String()

    users = graphene.List(UserType, entitled=graphene.Boolean())

    node = graphene.Field(NodeType)
    cluster = graphene.Field(ClusterType)
    datapool = graphene.Field(DatapoolType)
    template = graphene.Field(TemplateType)

    keep_vms_on = graphene.Boolean()
    create_thin_clones = graphene.Boolean()

    async def resolve_controller(self, info):
        controller_obj = await Controller.get(self.controller)
        return ControllerType(**controller_obj.__values__)

    async def resolve_users(self, _info, entitled=True):
        if entitled:
            users_data = await User.join(PoolUsers, User.id == PoolUsers.user_id).select().where(
                 PoolUsers.pool_id == self.pool_id).gino.all()
        else:
            subquery = PoolUsers.select('user_id').where(PoolUsers.pool_id == self.pool_id)
            users_data = await User.select('username', 'email', 'id').where(User.id.notin_(subquery)).gino.all()

        user_type_list = [
            UserType(id=user.id, username=user.username, email=user.email)
            for user in users_data
        ]
        return user_type_list

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
                 'status': pool_obj.status
                 }
    return PoolType(**pool_dict)


class PoolQuery(graphene.ObjectType):

    pools = graphene.List(PoolType, ordering=graphene.String())
    pool = graphene.Field(PoolType, pool_id=graphene.String())

    @superuser_required
    async def resolve_pools(self, info, ordering=None):
        # Сортировка может быть по полю модели Pool, либо по Pool.EXTRA_ORDER_FIELDS
        pools = await Pool.get_pools(ordering=ordering)
        objects = [
            pool_obj_to_type(pool)
            for pool in pools
        ]
        return objects

    @superuser_required
    async def resolve_pool(self, _info, pool_id):
        pool = await Pool.get_pool(pool_id)
        if not pool:
            raise SimpleError('No such pool.')
        return pool_obj_to_type(pool)


# --- --- --- --- ---
# Pool mutations
class DeletePoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        pool_id = graphene.UUID()
        full = graphene.Boolean(required=False)

    ok = graphene.Boolean()

    @staticmethod
    async def delete_pool(pool, full=False):
        if full:
            is_deleted = await pool.full_delete()
        else:
            is_deleted = await pool.soft_delete()

        return is_deleted

    @superuser_required
    async def mutate(self, info, pool_id, full=False):
        # Нет запуска валидации, т.к. нужна сущность пула далее - нет смысла запускать запрос 2жды.
        pool = await Pool.get(pool_id)
        if not pool:
            raise SimpleError('No such pool.')

        try:
            pool_type = await pool.pool_type

            # В случае автоматическогог пула получаем лок
            if pool_type == Pool.PoolTypes.AUTOMATED:
                template_id = await pool.template_id
                pool_lock = pool_task_manager.get_pool_lock(str(pool_id))
                async with pool_lock.lock:
                    # останавливаем таски связанные с пулом
                    await pool_task_manager.cancel_all_tasks_for_pool(str(pool_id))
                    # удаляем пул
                    is_deleted = await DeletePoolMutation.delete_pool(pool, full)
                    # убираем из памяти локи
                    await pool_task_manager.remove_pool_data(str(pool_id), str(template_id))
            # В случае стат пула удаляем без локов.
            else:
                is_deleted = await DeletePoolMutation.delete_pool(pool, full)

            return DeletePoolMutation(ok=is_deleted)
        except Exception as e:
            raise e


# --- --- --- --- ---
# Static pool mutations
class CreateStaticPoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        verbose_name = graphene.String(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @staticmethod
    async def fetch_veil_vm_data_list(vm_ids):
        # TODO: не пересена в модель, потому что есть предложение вообще отказаться от такой проверки.
        #  Более удобным вариантом кажется хранить ресурсы в кеше и валидировать их из него.
        controller_adresses = await Controller.get_controllers_addresses()
        # create list of all vms on controllers
        all_vm_veil_data_list = []
        for controller_address in controller_adresses:
            vm_http_client = await VmHttpClient.create(controller_address, '')
            try:
                single_vm_veil_data_list = await vm_http_client.fetch_vms_list()
                # add data about controller address
                for vm_veil_data in single_vm_veil_data_list:
                    vm_veil_data['controller_address'] = controller_address
                all_vm_veil_data_list.extend(single_vm_veil_data_list)
            except (HttpError, OSError):
                print('HttpError')
                pass

        # find vm veil data by id
        vm_veil_data_list = []
        for vm_id in vm_ids:
            try:
                data = next(veil_vm_data for veil_vm_data in all_vm_veil_data_list if veil_vm_data['id'] == str(vm_id))
                vm_veil_data_list.append(data)
            except StopIteration:
                raise SimpleError('ВМ с id {} не найдена ни на одном из известных контроллеров'.format(vm_id))
        return vm_veil_data_list

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        pool = None
        vm_ids = kwargs['vm_ids']
        verbose_name = kwargs['verbose_name']

        application_log.debug('StaticPool: Get vm info')
        veil_vm_data_list = await CreateStaticPoolMutation.fetch_veil_vm_data_list(vm_ids)

        application_log.debug('StaticPool: Check that all vms are on the same node')
        first_vm_data = veil_vm_data_list[0]

        # TODO: move to validator?
        if not all(vm_data['node']['id'] == first_vm_data['node']['id'] for vm_data in veil_vm_data_list):
            raise SimpleError("Все ВМ должны находится на одном сервере")

        # All VMs are on the same node and cluster, all VMs have the same datapool
        # so we can take this data from the first item
        controller_ip = first_vm_data['controller_address']
        node_id = first_vm_data['node']['id']

        application_log.debug('StaticPool: Determine cluster')
        resources_http_client = await ResourcesHttpClient.create(controller_ip)
        node_data = await resources_http_client.fetch_node(node_id)
        cluster_id = node_data['cluster']

        application_log.debug('StaticPool: Determine datapool')
        vm_http_client = await VmHttpClient.create(controller_ip, first_vm_data['id'])
        disks_list = await vm_http_client.fetch_vdisks_list()

        try:
            datapool_id = disks_list[0]['datapool']['id']
        except IndexError as ie:
            datapool_id = None
            application_log.error(ie)

        try:
            await Vm.enable_remote_accesses(controller_ip, vm_ids)
            application_log.debug('StaticPool: Determine datapool')
            pool = await StaticPool.create(verbose_name=verbose_name,
                                           controller_ip=controller_ip,
                                           cluster_id=cluster_id,
                                           node_id=node_id,
                                           datapool_id=datapool_id)

            application_log.debug('StaticPool: Objects on VDI DB created.')
            # Add VMs to db
            for vm_info in veil_vm_data_list:
                application_log.debug('VM info {}'.format(vm_info))
                await Vm.create(id=vm_info['id'],
                                template_id=None,
                                pool_id=pool.id,
                                controller_address=controller_ip,
                                created_by_vdi=False,
                                verbose_name=vm_info['verbose_name'])

            # response
            vms = [VmType(id=vm_id) for vm_id in vm_ids]
            await pool.activate()

            application_log.debug('StaticPool: pool {} created.'.format(verbose_name))
            await Event.create_info('Static pool {name} created.'.format(name=verbose_name))
        except Exception as E:  # Возможные исключения: дубликат имени или вм id, сетевой фейл enable_remote_accesses
            application_log.error('Failed to create static pool {}.'.format(verbose_name))
            application_log.debug(E)
            await Event.create_error('Failed to create static pool {}.'.format(verbose_name))
            if pool:
                await pool.deactivate()
            return {'ok': False}
        return {
            'pool': PoolType(pool_id=pool.id, verbose_name=verbose_name, vms=vms),
            'ok': True
        }


class AddVmsToStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise SimpleError("Список ВМ не должен быть пустым")

        pool_data = await Pool.select('controller', 'node_id').where(Pool.id == pool_id).gino.first()
        (controller_id, node_id) = pool_data
        controller_address = await Controller.select('address').where(Controller.id == controller_id).gino.scalar()

        # vm checks
        vm_http_client = await VmHttpClient.create(controller_address, '')
        all_vms_on_node = await vm_http_client.fetch_vms_list(node_id=node_id)

        all_vm_ids_on_node = [vmachine['id'] for vmachine in all_vms_on_node]
        used_vm_ids = await Vm.get_all_vms_ids()  # get list of vms which are already in pools

        for vm_id in vm_ids:
            # check if vm exists and it is on the correct node
            if str(vm_id) not in all_vm_ids_on_node:
                raise SimpleError('ВМ {} находится на сервере отличном от сервера пула'.format(vm_id))
            # check if vm is free (not in any pool)
            if vm_id in used_vm_ids:
                raise SimpleError('ВМ {} уже находится в одном из пулов'.format(vm_id))

        # remote access
        await Vm.enable_remote_accesses(controller_address, vm_ids)

        # Add VMs to db
        for vm_info in all_vms_on_node:
            await Vm.create(id=vm_info['id'],
                            pool_id=pool_id,
                            controller_address=controller_address,
                            created_by_vdi=False,
                            verbose_name=vm_info['verbose_name'])

        return {
            'ok': True
        }


class RemoveVmsFromStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.ID, required=True)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise SimpleError("Список ВМ не должен быть пустым")

        # vms check
        # get list of vms ids which are in pool_id
        vms_ids_in_pool = await Vm.get_vms_ids_in_pool(pool_id)

        # check if given vm_ids in vms_ids_in_pool
        for vm_id in vm_ids:
            if vm_id not in vms_ids_in_pool:
                raise SimpleError('ВМ не принадлежит заданному пулу'.format(vm_id))

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

    ok = graphene.Boolean()

    @classmethod
    @superuser_required
    async def mutate(cls, _root, _info, **kwargs):
        await cls.validate_agruments(**kwargs)
        ok = await StaticPool.soft_update(kwargs['pool_id'], kwargs.get('verbose_name'), kwargs.get('keep_vms_on'))
        msg = 'Static pool {id} updated.'.format(id=kwargs['pool_id'])
        await Event.create_info(msg)
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
        max_amount_of_create_attempts = graphene.Int(default_value=15)
        initial_size = graphene.Int(default_value=1)
        reserve_size = graphene.Int(default_value=1)
        total_size = graphene.Int(default_value=1)
        vm_name_template = graphene.String(default_value='')

        create_thin_clones = graphene.Boolean(default_value=True)

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        try:
            automated_pool = await AutomatedPool.create(**kwargs)
        except UniqueViolationError as E:
            await Event.create_error('Failed to create automated pool.', entity_list=Pool().entity_list)
            raise SimpleError(E)

        # add data for protection
        pool_task_manager.add_new_pool_data(str(automated_pool.id), str(automated_pool.template_id))
        # start task
        native_loop = asyncio.get_event_loop()
        pool_lock = pool_task_manager.get_pool_lock(str(automated_pool.id))
        pool_lock.create_pool_task = native_loop.create_task(automated_pool.init_pool())

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
            raise ValidationError('Максимальное количество создаваемых ВМ не может быть меньше '
                                  'начального количества ВМ')
        if value < min_size or value > max_vm_amount:
            raise ValidationError('Максимальное количество создаваемых ВМ должно быть в интервале [{} {}]'.
                                  format(min_size, max_vm_amount))
        if total_size and value <= total_size:
            raise ValidationError('Максимальное количество создаваемых ВМ не может быть уменьшено.')
        return value

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        automated_pool = await AutomatedPool.get(kwargs['pool_id'])
        if automated_pool:
            await automated_pool.soft_update(verbose_name=kwargs.get('verbose_name'),
                                             reserve_size=kwargs.get('reserve_size'),
                                             total_size=kwargs.get('total_size'),
                                             vm_name_template=kwargs.get('vm_name_template'),
                                             keep_vms_on=kwargs.get('keep_vms_on'),
                                             create_thin_clones=kwargs.get('create_thin_clones'))
            automated_pool = await AutomatedPool.get(kwargs['pool_id'])
            msg = 'Automated pool {name} updated.'.format(name=automated_pool.verbose_name)
            await Event.create_info(msg)
            application_log.debug('Automated pool {} updated.'.format(automated_pool.verbose_name))
            return UpdateAutomatedPoolMutation(ok=True)
        return UpdateAutomatedPoolMutation(ok=False)


# --- --- --- --- ---
# pools <-> users relations
class AddPoolPermissionsMutation(graphene.Mutation):

    class Arguments:
        pool_id = graphene.ID()
        users = graphene.List(graphene.ID)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, pool_id, users):
        async with db.transaction():
            if users:
                for user in users:
                    await PoolUsers.create(pool_id=pool_id, user_id=user)

        return {'ok': True}


class DropPoolPermissionsMutation(graphene.Mutation):

    class Arguments:
        pool_id = graphene.ID()
        users = graphene.List(graphene.ID)
        free_assigned_vms = graphene.Boolean()

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, pool_id, users, free_assigned_vms=True):
        if users:
            async with db.transaction():
                # remove entitlements # PoolUsers.user_id.in_(users) and
                await PoolUsers.delete.where(
                    (PoolUsers.user_id.in_(users)) & (PoolUsers.pool_id == pool_id)).gino.status()

                # free vms in pool from users
                if free_assigned_vms:
                    # todo: похоже у нас в БД изъян. Нужно чтоб в таблице Vm хранились id юзеров а не имена
                    subquery = User.select('username').where(User.id.in_(users))

                    await Vm.update.values(username=None).where(
                        (Vm.username.in_(subquery)) & (Vm.pool_id == pool_id)).gino.status()

        return {'ok': True}


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

    entitleUsersToPool = AddPoolPermissionsMutation.Field()
    removeUserEntitlementsFromPool = DropPoolPermissionsMutation.Field()


pool_schema = graphene.Schema(query=PoolQuery,
                              mutation=PoolMutations,
                              auto_camelcase=False)
