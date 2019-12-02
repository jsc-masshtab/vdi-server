# -*- coding: utf-8 -*-
import re
import graphene
from tornado.httpclient import HTTPClientError  # TODO: точно это нужно тут?
from graphql.error.located_error import GraphQLLocatedError

from database import StatusGraphene
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, HttpError, ValidationError, VmCreationError
from common.utils import make_graphene_type

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

from asyncpg import UniqueViolationError

from database import db
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
        print('user_type_list', user_type_list)
        return user_type_list

    async def resolve_vms(self, _info):
        await self._build_vms_list()
        return self.vms

    async def resolve_node(self, _info):
        controller_address = await Pool.get_controller_ip(self.pool_id)
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        node_id = await Pool.select('node_id').where(Pool.pool_id == self.pool_id).gino.scalar()

        node_data = await resources_http_client.fetch_node(node_id)
        node_type = make_graphene_type(NodeType, node_data)
        node_type.controller = ControllerType(address=controller_address)
        return node_type

    async def resolve_cluster(self, _info):
        controller_address = await Pool.get_controller_ip(self.pool_id)
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        cluster_id = await Pool.select('cluster_id').where(Pool.pool_id == self.pool_id).gino.scalar()

        cluster_data = await resources_http_client.fetch_cluster(cluster_id)
        cluster_type = make_graphene_type(ClusterType, cluster_data)
        cluster_type.controller = ControllerType(address=controller_address)
        return cluster_type

    async def resolve_datapool(self, _info):
        controller_address = await Pool.get_controller_ip(self.pool_id)
        resources_http_client = await ResourcesHttpClient.create(controller_address)
        datapool_id = await AutomatedPool.select('datapool_id').where(
            AutomatedPool.automated_pool_id == self.pool_id).gino.scalar()

        try:
            datapool_data = await resources_http_client.fetch_datapool(datapool_id)
            datapool_type = make_graphene_type(DatapoolType, datapool_data)
            datapool_type.controller = ControllerType(address=controller_address)
            return datapool_type
        except (HTTPClientError, HttpError):
            # либо датапул изчес с контроллера, либо попытка получить датапул для статического пула
            return None

    async def resolve_template(self, _info):
        controller_address = await Pool.get_controller_ip(self.pool_id)
        template_id = await AutomatedPool.select('template_id').where(
            AutomatedPool.automated_pool_id == self.pool_id).gino.scalar()
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
            vms_data = await Vm.select("id").where((Vm.pool_id == self.pool_id)).gino.all()
            controller_address = await Pool.get_controller_ip(self.pool_id)
            for (vm_id,) in vms_data:
                vm_http_client = await VmHttpClient.create(controller_address, vm_id)
                try:
                    veil_info = await vm_http_client.info()
                    # create graphene type
                    vm_type = VmQuery.veil_vm_data_to_graphene_type(veil_info, controller_address)
                except (HTTPClientError, HttpError):
                    vm_type = VmType(id=vm_id, controller=ControllerType(address=controller_address))
                    vm_type.veil_info = None
                self.vms.append(vm_type)


class PoolQuery(graphene.ObjectType):

    pools = graphene.List(PoolType, ordering=graphene.String())
    pool = graphene.Field(PoolType, pool_id=graphene.String())

    async def resolve_pools(self, info, ordering=None):
        # Сортировка может быть по полю модели Pool, либо по Pool.EXTRA_ORDER_FIELDS
        pools = await Pool.get_pools(ordering=ordering)
        objects = [
            PoolType(**pool)
            for pool in pools
        ]
        return objects

    async def resolve_pool(self, _info, pool_id):
        pool = await Pool.get_pool(pool_id)
        if not pool:
            raise SimpleError('No such pool.')
        return PoolType(**pool)


# --- --- --- --- ---
# Pool mutations
class DeletePoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        pool_id = graphene.UUID()

    ok = graphene.Boolean()

    async def mutate(self, info, pool_id):

        # Меняем статус пула. Не нравится идея удалять записи имеющие внешние зависимости, которые не удалить,
        # например запущенные виртуалки.
        await Pool.soft_delete(pool_id)
        msg = 'Pool {id} deactivated.'.format(id=pool_id)
        await Event.create_info(msg)
        return DeletePoolMutation(ok=True)


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
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        pool = None
        vm_ids = kwargs['vm_ids']
        verbose_name = kwargs['verbose_name']
        # get vm info
        veil_vm_data_list = await CreateStaticPoolMutation.fetch_veil_vm_data_list(vm_ids)
        # Check that all vms are on the same node
        first_vm_data = veil_vm_data_list[0]
        # TODO: move to validator?
        if not all(vm_data['node']['id'] == first_vm_data['node']['id'] for vm_data in veil_vm_data_list):
            raise SimpleError("Все ВМ должны находится на одном сервере")
        # All VMs are on the same node and cluster so we can take this data from the first item
        controller_ip = first_vm_data['controller_address']
        node_id = first_vm_data['node']['id']
        # determine cluster
        resources_http_client = await ResourcesHttpClient.create(controller_ip)
        node_data = await resources_http_client.fetch_node(node_id)
        cluster_id = node_data['cluster']
        try:
            await Vm.enable_remote_accesses(controller_ip, vm_ids)
            pool = await StaticPool.create(verbose_name=verbose_name,
                                           controller_ip=controller_ip,
                                           cluster_id=cluster_id,
                                           node_id=node_id)
            # add vms to db
            for vm_id in vm_ids:
                await Vm.create(id=vm_id, pool_id=pool.static_pool_id)

            # response
            vms = [VmType(id=vm_id) for vm_id in vm_ids]
            await pool.activate()
            msg = 'Static pool {id} created.'.format(id=pool.pool_id)
            await Event.create_info(msg)
        except Exception as E:  # Возможные исключения: дубликат имени или вм id, сетевой фейл enable_remote_accesses
            await Event.create_error('Failed to create static pool.')
            print(E)
            if pool:
                await pool.deactivate()
            return E
        return {
            'pool': PoolType(pool_id=pool.static_pool_id, verbose_name=verbose_name, vms=vms),
            'ok': True
        }


class AddVmsToStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise SimpleError("Список ВМ не должен быть пустым")

        pool_data = await Pool.select('controller', 'node_id').where(Pool.pool_id == pool_id).gino.first()
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

        # add vms to db
        for vm_id in vm_ids:
            await Vm.create(id=vm_id, pool_id=pool_id)

        return {
            'ok': True
        }


class RemoveVmsFromStaticPoolMutation(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.ID, required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise SimpleError("Список ВМ не должен быть пустым")

        # vms check
        # get list of vms ids which are in pool_id
        vms_ids_in_pool = await Vm.get_vms_ids_in_pool(pool_id)
        print('vms_ids_in_pool', vms_ids_in_pool)

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
        max_amount_of_create_attempts = graphene.Int(default_value=2)
        initial_size = graphene.Int(default_value=1)
        reserve_size = graphene.Int(default_value=0)
        total_size = graphene.Int(default_value=1)
        vm_name_template = graphene.String(default_value='')

        create_thin_clones = graphene.Boolean(default_value=True)

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        pool = None
        try:
            automated_pool = await AutomatedPool.create(**kwargs)

            await automated_pool.add_initial_vms()
            await automated_pool.activate()

            pool = await Pool.get_pool(automated_pool.automated_pool_id)
            msg = 'Automated pool {id} created.'.format(id=pool.pool_id)
            await Event.create_info(msg)
        except (UniqueViolationError, VmCreationError) as E:  # Возможные исключения: дубликат имени пула,VmCreationError
            print('exp__', E.__class__.__name__)
            await Event.create_error('Failed to create automated pool.')
            if pool:
                await pool.deactivate()
            raise SimpleError(E)
        return CreateAutomatedPoolMutation(
                pool=PoolType(**pool),
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

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        ok = await AutomatedPool.soft_update(kwargs['pool_id'], kwargs.get('verbose_name'), kwargs.get('reserve_size'),
                                             kwargs.get('total_size'), kwargs.get('vm_name_template'),
                                             kwargs.get('keep_vms_on'), kwargs.get('create_thin_clones'))
        msg = 'Dynamic pool {id} updated.'.format(id=kwargs['pool_id'])
        await Event.create_info(msg)
        return UpdateAutomatedPoolMutation(ok=ok)


# --- --- --- --- ---
# pools <-> users relations
class AddPoolPermissionsMutation(graphene.Mutation):

    class Arguments:
        pool_id = graphene.ID()
        users = graphene.List(graphene.ID)

    ok = graphene.Boolean()

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
