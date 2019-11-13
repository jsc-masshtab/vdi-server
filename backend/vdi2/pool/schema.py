# -*- coding: utf-8 -*-
import re
import graphene
from tornado.httpclient import HTTPClientError  # TODO: точно это нужно тут?

from database import StatusGraphene
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, HttpError, ValidationError
from common.utils import make_graphene_type

from auth.schema import UserType
from auth.models import User

from vm.schema import VmType, VmQuery, TemplateType
from vm.models import Vm
from vm.veil_client import VmHttpClient

from controller.schema import ControllerType
from controller.models import Controller

from controller_resources.veil_client import ResourcesHttpClient
from controller_resources.schema import ClusterType, NodeType, DatapoolType

from pool.models import AutomatedPool, StaticPool, Pool
# TODO: отсутствует валидация входящих ресурсов вроде node_uid, cluster_uid и т.п. Ранее шла речь,
#  о том, что мы будем кешированно хранить какие-то ресурсы полученные от ECP Veil. Возможно стоит
#  обращаться к этому хранилищу для проверки корректности присланных ресурсов. Аналогичный принцип
#  стоит применить и к статическим пулам (вместо похода на вейл для проверки присланных параметров).


async def check_and_return_pool_data(pool_id, pool_type=None):
    # TODO: а это точно нужно?
    # TODO: remove raw sql, rewrite
    # check if pool exists
    async with db.connect() as conn:
        qu = 'SELECT * FROM pool WHERE id = $1', pool_id
        pool_data = await conn.fetch(*qu)
        if not pool_data:
            raise SimpleError('Не найден пул с указанным id')
        [pool_data] = pool_data
        pool_data_dict = dict(pool_data.items())

    # if pool_type provided then check if pool has required type
    if pool_type and pool_data_dict['desktop_pool_type'] != pool_type:
        raise SimpleError('Не найден пул с указанным id и типом {}'.format(pool_type))

    return pool_data_dict


class PoolValidator(MutationValidation):
    """Валидатор для сущности Pool"""

    @staticmethod
    async def validate_id(obj_dict, value):
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
        pool_id = obj_dict.get('id')
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

        pool_id = obj_dict.get('id')
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
    id = graphene.UUID()
    verbose_name = graphene.String()
    status = StatusGraphene()
    POOL_TYPE = graphene.String()
    cluster_id = graphene.UUID()
    node_id = graphene.UUID()
    controller = graphene.Field(ControllerType)

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

    # TODO: дополнить внешними сущностями
    # users = graphene.List(UserType, entitled=graphene.Boolean())
    # vms = graphene.List(VmType)
    # node = graphene.Field(NodeType)
    # cluster = graphene.Field(ClusterType)
    # datapool = graphene.Field(DatapoolType)
    # template = graphene.Field(TemplateType)

    async def resolve_controller(self, info):
        controller_obj = await Controller.get(self.controller)
        return ControllerType(**controller_obj.__values__)

    # async def resolve_users(self, _info, entitled=True):
    #     # users who are entitled to pool
    #     if entitled:
    #         users_data = await User.join(PoolUsers, User.id == PoolUsers.user_id).select().where(
    #              PoolUsers.pool_id == self.id).gino.all()
    #     # users who are NOT entitled to pool
    #     else:
    #         subquery = PoolUsers.query(PoolUsers.user_id).where(PoolUsers.pool_id == self.id)
    #         users_data = User.filter(User.id.notin_(subquery)).gino.all()
    #     print('users_data', users_data)
    #     # todo: it will not work until model and grapnene feilds are syncronized
    #     uset_type_list = [
    #         UserType(**user.__values__)
    #         for user in users_data
    #     ]
    #     return uset_type_list

    async def resolve_vms(self, _info):
        await self._build_vms_list()
        return self.vms

    # async def resolve_pool_resources_names(self, _info):
    #
    #     list_of_requested_fields = get_selections(_info)
    #     # get resources ids from db
    #     pool_data_keys_list = ['controller', 'cluster_id', 'node_id', 'datapool_id', 'template_id']
    #     pool_data_tuple = await Pool.select(pool_data_keys_list).where(Pool.id == self.id).gino.all()
    #
    #     pool_data = dict(zip(pool_data_keys_list, pool_data_tuple))
    #
    #     # requests to controller
    #     resources_http_client = await ResourcesHttpClient.create(pool_data['controller_ip'])
    #     try:
    #         if 'cluster_name' in list_of_requested_fields:
    #             veil_info = await resources_http_client.fetch_cluster(cluster_id=pool_data['cluster_id'])
    #             cluster_name = veil_info['verbose_name']
    #
    #         if 'node_name' in list_of_requested_fields:
    #             veil_info = await resources_http_client.fetch_node(['node_id'])
    #             node_name = veil_info['verbose_name']
    #
    #         if 'datapool_name' in list_of_requested_fields:
    #             veil_info = await resources_http_client.fetch_datapool(pool_data['datapool_id'])
    #             datapool_name = veil_info['verbose_name']
    #
    #         if 'template_name' in list_of_requested_fields:
    #             vm_http_client = await VmHttpClient.create(pool_data['controller_ip'], pool_data['template_id'])
    #             veil_info = await vm_http_client.info()
    #             template_name = veil_info['verbose_name']
    #
    #             return PoolResourcesNames(cluster_name=cluster_name, node_name=node_name,
    #                                       datapool_name=datapool_name, template_name=template_name)
    #     except HTTPClientError:
    #         return PoolResourcesNames(cluster_name=DEFAULT_NAME, node_name=DEFAULT_NAME,
    #                                   datapool_name=DEFAULT_NAME, template_name=DEFAULT_NAME)
    #
    # async def resolve_node(self, _info):
    #     resources_http_client = await ResourcesHttpClient.create(self.controller.address)
    #
    #     node_id = await Pool.select('node_id').where(Pool.id == self.id).gino.scalar()
    #     node_data = await resources_http_client.fetch_node(node_id)
    #     node_type = make_graphene_type(NodeType, node_data)
    #     node_type.controller = ControllerType(address=self.controller.address)
    #     return node_type
    #
    # async def resolve_cluster(self, _info):
    #     resources_http_client = await ResourcesHttpClient.create(self.controller.address)
    #
    #     cluster_id = await Pool.select('cluster_id').where(Pool.id == self.id).gino.scalar()
    #     cluster_data = await resources_http_client.fetch_cluster(cluster_id)
    #     cluster_type = make_graphene_type(ClusterType, cluster_data)
    #     cluster_type.controller = ControllerType(address=self.controller.address)
    #     return cluster_type
    #
    # async def resolve_datapool(self, _info):
    #     resources_http_client = await ResourcesHttpClient.create(self.controller.address)
    #
    #     datapool_id = await Pool.select('datapool_id').where(Pool.id == self.id).gino.scalar()
    #     datapool_data = await resources_http_client.fetch_datapool(datapool_id)
    #     datapool_type = make_graphene_type(DatapoolType, datapool_data)
    #     datapool_type.controller = ControllerType(address=self.controller.address)
    #     return datapool_type
    #
    # async def resolve_template(self, _info):
    #     template_id = await Pool.select('template_id').where(Pool.id == self.id).gino.scalar()
    #     vm_http_client = await VmHttpClient.create(self.controller.address, template_id)
    #     veil_info = await vm_http_client.info()
    #     return VmQuery.veil_template_data_to_graphene_type(veil_info, self.controller.address)
    #
    # async def _build_vms_list(self):
    #     if not self.vms:
    #         self.vms = []
    #         vms_data = await Vm.select("id").where((Vm.pool_id == self.id)).gino.all()
    #         for (vm_id,) in vms_data:
    #             vm_http_client = await VmHttpClient.create(self.controller.address, vm_id)
    #             try:
    #                 veil_info = await vm_http_client.info()
    #                 # create graphene type
    #                 vm_type = VmQuery.veil_vm_data_to_graphene_type(veil_info, self.controller.address)
    #             except HTTPClientError:
    #                 vm_type = VmType(id=vm_id, controller=ControllerType(address=self.controller.address))
    #                 vm_type.veil_info = None
    #             self.vms.append(vm_type)


class PoolQuery(graphene.ObjectType):
    # TODO: описать возможные типы сортировок
    # TODO: сортировка данных
    pools = graphene.List(PoolType, ordering=graphene.String(), reversed_order=graphene.Boolean())
    pool = graphene.Field(PoolType, id=graphene.String(), controller_address=graphene.String())

    # async with db.connect() as conn:
    #     # sort items if required
    #     if ordering:
    #         # is reversed
    #         if reversed_order is not None:
    #             sort_order = 'DESC' if reversed_order else 'ASC'
    #         else:
    #             sort_order = 'ASC'
    #
    #         # determine sql query
    #         if ordering == 'name':
    #             qu = "SELECT * FROM pool ORDER BY name {}".format(sort_order)
    #             pools = await
    #             conn.fetch(qu)
    #             return PoolMixin._pool_db_data_to_pool_type_list(pools)
    #         elif ordering == 'controller':
    #             qu = "SELECT * FROM pool ORDER BY controller_ip {}".format(sort_order)
    #             pools = await
    #             conn.fetch(qu)
    #             return PoolMixin._pool_db_data_to_pool_type_list(pools)
    #         elif ordering == 'vms':
    #             qu = "SELECT pool.* FROM pool LEFT JOIN vm " \
    #                  "ON pool.id = vm.pool_id GROUP BY pool.id ORDER BY COUNT(vm.id) {}".format(sort_order)
    #             pools = await
    #             conn.fetch(qu)
    #             return PoolMixin._pool_db_data_to_pool_type_list(pools)
    #         elif ordering == 'users':
    #             qu = "SELECT pool.* FROM pool LEFT JOIN pools_users " \
    #                  "ON pool.id = pools_users.pool_id GROUP BY pool.id ORDER BY COUNT(pools_users.username)" \
    #                  " {}".format(sort_order)
    #             pools = await
    #             conn.fetch(qu)
    #             return PoolMixin._pool_db_data_to_pool_type_list(pools)
    #         elif ordering == 'desktop_pool_type':
    #             qu = "SELECT * FROM pool ORDER BY desktop_pool_type {}".format(sort_order)
    #             pools = await
    #             conn.fetch(qu)
    #             return PoolMixin._pool_db_data_to_pool_type_list(pools)
    #         elif ordering == 'status':
    #             qu = "SELECT * FROM pool"
    #             pools = await
    #             conn.fetch(qu)
    #             pool_type_list = PoolMixin._pool_db_data_to_pool_type_list(pools)
    #
    #             for pool_type in pool_type_list:
    #                 await
    #                 pool_type.determine_pool_status()
    #             reverse = reversed_order if reversed_order is not None else False
    #             pool_type_list = sorted(pool_type_list, key=lambda item: item.status, reverse=reverse)
    #             return pool_type_list
    #         else:
    #             raise SimpleError('Неверный параметр сортировки')
    #     else:
    #         qu = "SELECT * FROM pool"
    #         pools = await
    #         conn.fetch(qu)
    #         return PoolMixin._pool_db_data_to_pool_type_list(pools)

    async def resolve_pools(self, info, ordering=None, reversed_order=None):
        pools = await Pool.get_pools()
        objects = [
            PoolType(**pool)
            for pool in pools
        ]
        return objects

    async def resolve_pool(self, _info, id):
        pool = await Pool.get_pool(id)
        if not pool:
            raise SimpleError('No such pool.')
        return PoolType(**pool)


# --- --- --- --- ---
# Pool mutations
class DeletePoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        id = graphene.UUID()

    ok = graphene.Boolean()

    async def mutate(self, info, id):

        # Меняем статус пула. Не нравится идея удалять записи имеющие большое количество зависимостей,
        # например запущенные виртуалки.
        await Pool.soft_delete(id)
        return DeletePoolMutation(ok=True)


# --- --- --- --- ---
# Static pool mutations
class CreateStaticPoolMutation(graphene.Mutation, PoolValidator):
    class Arguments:
        verbose_name = graphene.String(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    Output = PoolType

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
                data = next(veil_vm_data for veil_vm_data in all_vm_veil_data_list if veil_vm_data['id'] == vm_id)
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
        # Check that all vms are on the same node (Условие поставленное начальством, насколько я помню)
        first_vm_data = veil_vm_data_list[0]
        # TODO: move to validator?
        if not all(x == first_vm_data for x in veil_vm_data_list):
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
                await Vm.create(id=vm_id, pool_id=pool.uid)

            # response
            vms = [VmType(id=vm_id) for vm_id in vm_ids]
            await pool.activate()
        except Exception as E:
            # TODO: широкий exception потому, что пока нет ошибки от монитора ресурсов. эксепшены нужно ограничить.
            print(E)
            if pool:
                await pool.deactivate()
            return CreateStaticPoolMutation(
                pool=None)
        return PoolType(id=pool.uid, name=verbose_name, vms=vms,
                        )


class AddVmsToStaticPool(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.UUID, required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise SimpleError("Список ВМ не должен быть пустым")

        # todo: Запрос к модели статич. пула
        pool_data = await Pool.select('controller', 'node_id').where(Pool.id == pool_id).gino.all()
        controller_id, node_id = pool_data
        controller_address = Controller.select('address').where(Controller.id == controller_id).gino.scalar()

        # vm checks
        vm_http_client = await VmHttpClient.create(controller_address, '')
        all_vms_on_node = await vm_http_client.fetch_vms_list(node_id=node_id)

        all_vm_ids_on_node = [vmachine['id'] for vmachine in all_vms_on_node]
        used_vm_ids = await Vm.get_all_vms_ids()  # get list of vms which are already in pools

        for vm_id in vm_ids:
            # check if vm exists and it is on the correct node
            if vm_id not in all_vm_ids_on_node:
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


class RemoveVmsFromStaticPool(graphene.Mutation):
    class Arguments:
        pool_id = graphene.ID(required=True)
        vm_ids = graphene.List(graphene.ID, required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, pool_id, vm_ids):
        if not vm_ids:
            raise SimpleError("Список ВМ не должен быть пустым")
        # pool checks todo: Запрос к модели статич. пула
        pool_object = await Pool.get_pool(pool_id)
        if not pool_object:
            raise SimpleError('Пул {} не существует'.format(pool_id))

        # vms check
        # get list of vms ids which are in pool_id
        vms_ids_in_pool = await Vm.get_vms_ids_in_pool(pool_id)
        print('vms_ids_in_pool', vms_ids_in_pool)

        # check if given vm_ids in vms_ids_in_pool
        for vm_id in vm_ids:
            if vm_id not in vms_ids_in_pool:
                raise SimpleError('ВМ не принадлежит заданному пулу'.format(vm_id))

        # remove vms
        await Vm.remove_vms(vm_ids)

        return {
            'ok': True
        }


# TODO: update StaticPool
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

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()

    @classmethod
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        pool = None
        try:
            automated_pool = await AutomatedPool.create(**kwargs)
            # TODO: в мониторе ресурсов нет происходит raise ошибки, если оно не создано
            await automated_pool.add_initial_vms()
            await automated_pool.activate()
            pool = await Pool.get_pool(automated_pool.automated_pool_id)
        except Exception as E:
            # TODO: широкий exception потому, что пока нет ошибки от монитора ресурсов. эксепшены нужно ограничить.
            if pool:
                await pool.deactivate()
            raise SimpleError(E)
        return CreateAutomatedPoolMutation(
                pool=PoolType(**pool),
                ok=True)


class UpdateAutomatedPoolMutation(graphene.Mutation, PoolValidator):
    """Перечень полей доступных для редактирования отдельно не рассматривалась. Перенесена логика из Confluence."""
    class Arguments:
        id = graphene.UUID(required=True)
        verbose_name = graphene.String()
        reserve_size = graphene.Int()
        total_size = graphene.Int()
        vm_name_template = graphene.String()

    pool = graphene.Field(lambda: PoolType)
    ok = graphene.Boolean()



    @classmethod
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        ok = await AutomatedPool.soft_update(kwargs['id'], kwargs.get('verbose_name'), kwargs.get('reserve_size'),
                                             kwargs.get('total_size'), kwargs.get('vm_name_template'))
        return UpdateAutomatedPoolMutation(ok=ok)


# --- --- --- --- ---
# Schema concatenation
class PoolMutations(graphene.ObjectType):
    addDynamicPool = CreateAutomatedPoolMutation.Field()
    addStaticPool = CreateStaticPoolMutation.Field()
    addVmsToStaticPool = AddVmsToStaticPool.Field()  # TODO: а это точно должно быть тут, а не в Vm?
    removeVmsFromStaticPool = RemoveVmsFromStaticPool.Field()  # TODO: а это точно должно быть тут, а не в Vm?
    removePool = DeletePoolMutation.Field()
    updateDynamicPool = UpdateAutomatedPoolMutation.Field()


pool_schema = graphene.Schema(query=PoolQuery,
                              mutation=PoolMutations,
                              auto_camelcase=False)
