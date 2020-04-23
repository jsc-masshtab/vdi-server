# -*- coding: utf-8 -*-
import asyncio
import uuid
from enum import Enum
from sqlalchemy import union_all, case, literal_column, desc, text, Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from asyncpg.exceptions import UniqueViolationError

from common.veil_errors import VmCreationError, PoolCreationError, HttpError, SimpleError, ValidationError
from common.veil_client import VeilHttpClient
from auth.license.utils import License
from settings import VEIL_WS_MAX_TIME_TO_WAIT
from database import db, Status, EntityType
from redis_broker import get_thin_clients_count
from controller.models import Controller
from pool.pool_task_manager import pool_task_manager

from resources_monitoring.handlers import WaiterSubscriptionObserver
from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from resources_monitoring.resources_monitoring_data import VDI_TASKS_SUBSCRIPTION
from resources_monitoring.internal_event_monitor import internal_event_monitor


from auth.models import User, Entity, EntityRoleOwner, Group, UserGroup
from vm.models import Vm
from vm.veil_client import VmHttpClient

from languages import lang_init
from journal.journal import Log as log


_ = lang_init()


class Pool(db.Model):
    """На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах)."""

    class PoolTypes:
        """Доступные типы подключения служб каталогов."""

        AUTOMATED = 'AUTOMATED'
        STATIC = 'STATIC'

    class PoolConnectionTypes(Enum):
        """Типы подключений к VM доступные пулу."""

        SPICE = 'SPICE'
        RDP = 'RDP'
        NATIVE_RDP = 'NATIVE_RDP'

    __tablename__ = 'pool'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4, unique=True)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    cluster_id = db.Column(UUID(), nullable=False)
    node_id = db.Column(UUID(), nullable=False)
    datapool_id = db.Column(UUID(), nullable=True)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)
    controller = db.Column(UUID(), db.ForeignKey('controller.id', ondelete="CASCADE"), nullable=False)

    keep_vms_on = db.Column(db.Boolean(), nullable=False, default=False)
    connection_types = db.Column(ARRAY(AlchemyEnum(PoolConnectionTypes)), nullable=False, index=True)

    # ----- ----- ----- ----- ----- ----- -----
    # Constants:
    POOL_TYPE_LABEL = 'pool_type'
    EXTRA_ORDER_FIELDS = ['controller_address', 'users_count', 'vm_amount', 'pool_type']

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    async def possible_connection_types(self):
        return [connection_type for connection_type in self.PoolConnectionTypes if
                connection_type not in self.connection_types]

    @property
    def entity_type(self):
        return EntityType.POOL

    @property
    def entity(self):
        return {'entity_type': self.entity_type, 'entity_uuid': self.id}

    @property
    async def entity_obj(self):
        return await Entity.query.where(
            (Entity.entity_type == self.entity_type) & (Entity.entity_uuid == self.id)).gino.first()

    @property
    async def has_vms(self):
        """Проверяем наличие виртуальных машин"""

        vm_count = await db.select([db.func.count(Vm.id)]).where(
            Vm.pool_id == self.id).gino.scalar()
        if vm_count == 0:
            return False
        return True

    @property
    async def is_automated_pool(self):
        return await db.scalar(db.exists().where(AutomatedPool.id == self.id).select())

    @property
    async def pool_type(self):
        """Возвращает тип пула виртуальных машин"""
        # TODO: проверить используется ли
        is_automated = await self.is_automated_pool
        return Pool.PoolTypes.AUTOMATED if is_automated else Pool.PoolTypes.STATIC

    @property
    async def template_id(self):
        """Возвращает template_id для автоматического пула, либо null"""
        template_id = await AutomatedPool.select('template_id').where(
            AutomatedPool.id == self.id).gino.scalar()
        return template_id

    @classmethod
    def thin_client_limit_exceeded(cls):
        current_license = License()
        return get_thin_clients_count() >= current_license.thin_clients_limit

    @staticmethod
    def build_ordering(query, ordering=None):
        """Построение порядка сортировки"""

        if not ordering or not isinstance(ordering, str):
            return query

        # Определяем порядок сортировки по наличию "-" вначале строки
        if ordering.find('-', 0, 1) == 0:
            reversed_order = True
            ordering = ordering[1:]
        else:
            reversed_order = False

        # TODO: если сделать валидацию переданных полей на сортировку - try не нужен
        try:
            if ordering in Pool.EXTRA_ORDER_FIELDS:
                if ordering == 'controller_address':
                    query = query.order_by(desc(Controller.address)) if reversed_order else query.order_by(
                        Controller.address)
                elif ordering == 'users_count':
                    users_count = db.func.count(text('anon_1.entity_role_owner_user_id'))
                    query = query.order_by(desc(users_count)) if reversed_order else query.order_by(users_count)
                elif ordering == 'vm_amount':
                    vms_count = db.func.count(Vm.id)
                    query = query.order_by(desc(vms_count)) if reversed_order else query.order_by(vms_count)
                elif ordering == 'pool_type':
                    query = query.order_by(desc(text(Pool.POOL_TYPE_LABEL))) if reversed_order else query.order_by(
                        text(Pool.POOL_TYPE_LABEL))
            else:
                # Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order
                query = query.order_by(desc(getattr(Pool, ordering))) if reversed_order else query.order_by(
                    getattr(Pool, ordering))
        except AttributeError:
            raise SimpleError(_('Incorrect sorting option {}.').format(ordering))
        return query

    @staticmethod
    def get_pools_query(ordering=None, user_id=None, groups_ids_list=None, role_set=None):

        # Добавление в итоговый НД данных о признаке пула
        pool_type = case([(AutomatedPool.id.isnot(None), literal_column("'{}'".format(Pool.PoolTypes.AUTOMATED)))],
                         else_=literal_column("'{}'".format(Pool.PoolTypes.STATIC))).label(Pool.POOL_TYPE_LABEL)

        # Формирование общего селекта из таблиц пулов с добавлением принадлежности пула.
        query = db.select([
            Pool.id.label('master_id'),
            Pool.verbose_name,
            Pool.cluster_id,
            Pool.node_id,
            Pool.datapool_id,
            Pool.status,
            Pool.controller,
            Pool.keep_vms_on,
            AutomatedPool.template_id,
            AutomatedPool.min_size,
            AutomatedPool.max_size,
            AutomatedPool.max_vm_amount,
            AutomatedPool.increase_step,
            AutomatedPool.min_free_vms_amount,
            AutomatedPool.max_amount_of_create_attempts,
            AutomatedPool.initial_size,
            AutomatedPool.reserve_size,
            AutomatedPool.total_size,
            AutomatedPool.vm_name_template,
            AutomatedPool.os_type,
            AutomatedPool.create_thin_clones,
            pool_type,
            Pool.connection_types
        ])

        if ordering or user_id:
            # Добавляем пересечение с дополнительными внешними таблицами для возможности сортировки

            if user_id or role_set or groups_ids_list:
                if not role_set or not isinstance(role_set, set):
                    role_set = set()
                if not groups_ids_list or not isinstance(groups_ids_list, list):
                    groups_ids_list = list()
                permission_outer = False
                permissions_query = Entity.join(EntityRoleOwner.query.where(
                    (EntityRoleOwner.user_id == user_id) | (EntityRoleOwner.role.in_(role_set)) | (
                        EntityRoleOwner.group_id.in_(groups_ids_list))).alias())
            else:
                permission_outer = True
                permissions_query = Entity.join(EntityRoleOwner)

            query = query.select_from(
                Pool.join(AutomatedPool, isouter=True).join(Controller, isouter=True).join(Vm, isouter=True).join(
                    permissions_query.alias(), (Pool.id == text('entity_entity_uuid')),
                    isouter=permission_outer)).group_by(
                Pool.id,
                Pool.verbose_name,
                Pool.cluster_id,
                Pool.node_id,
                Pool.datapool_id,
                Pool.status,
                Pool.controller,
                Pool.keep_vms_on,
                AutomatedPool.id,
                AutomatedPool.template_id,
                AutomatedPool.min_size,
                AutomatedPool.max_size,
                AutomatedPool.max_vm_amount,
                AutomatedPool.increase_step,
                AutomatedPool.min_free_vms_amount,
                AutomatedPool.max_amount_of_create_attempts,
                AutomatedPool.initial_size,
                AutomatedPool.reserve_size,
                AutomatedPool.total_size,
                AutomatedPool.vm_name_template,
                AutomatedPool.os_type,
                AutomatedPool.create_thin_clones,
                Controller.address)

            # Сортировка
            query = Pool.build_ordering(query, ordering)
        else:
            # Делаем пересечение только с основными таблицами
            query = query.select_from(Pool.join(AutomatedPool, isouter=True))

        return query

    @staticmethod
    async def get_pool(pool_id, ordering=None):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        # TODO: проверить используется ли. Заменить на Pool.get?
        query = Pool.get_pools_query(ordering=ordering)
        query = query.where(Pool.id == pool_id)
        return await query.gino.first()

    @staticmethod
    async def get_pools(ordering=None):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        # TODO: проверить используется ли. Заменить на Pool.get?
        query = Pool.get_pools_query(ordering=ordering)
        return await query.gino.all()

    @staticmethod
    async def get_controller_ip(pool_id):
        # TODO: заменить на property controller_address
        query = db.select([Controller.address]).select_from(Controller.join(Pool)).where(
            Pool.id == pool_id)
        return await query.gino.scalar()

    async def get_vm_amount(self, only_free=False):
        """
        Нужно дорабатывать - отказаться от in и дублирования кода.
        :param only_free: учитываем только свободные VM
        :return: int
        """

        if only_free:
            entity_query = Entity.select('entity_uuid').where(
                (Entity.entity_type == EntityType.VM) & (
                    Entity.id.in_(EntityRoleOwner.select('id').where(EntityRoleOwner.user_id != None))))  # noqa

            vm_query = db.select([db.func.count(Vm.id)]).where(
                (Vm.pool_id == self.id) & (Vm.id.notin_(entity_query))).group_by(Vm.id)

            return await vm_query.gino.scalar()

        return await db.select([db.func.count()]).where(Vm.pool_id == self.id).gino.scalar()

    @property
    async def roles(self):
        """Уникальные роли назначенные пулу (без учета групп и пользователей)."""
        query = Entity.query.where((Entity.entity_type == EntityType.POOL) & (Entity.entity_uuid == self.id)).alias()
        filtered_query = EntityRoleOwner.join(query).select().alias()
        result_query = db.select([text('anon_1.role')]).select_from(filtered_query).group_by('role')
        return await result_query.gino.all()

    @property
    async def assigned_groups(self):
        """Группы назначенные пулу"""
        # TODO: возможно нужно добавить группы и пользователей обладающих Ролью
        query = Entity.query.where((Entity.entity_type == EntityType.POOL) & (Entity.entity_uuid == self.id)).alias()
        filtered_query = Group.join(EntityRoleOwner.join(query).alias()).select()
        return await filtered_query.gino.load(Group).all()

    @property
    async def possible_groups(self):
        query = Entity.query.where((Entity.entity_type == EntityType.POOL) & (Entity.entity_uuid == self.id)).alias()
        filtered_query = Group.join(EntityRoleOwner.join(query).alias(), isouter=True).select().where(text('anon_1.entity_role_owner_group_id is null'))  # noqa
        return await filtered_query.gino.load(Group).all()

    @property
    async def assigned_users(self):
        """Пользователи назначенные пулу (с учетом групп)"""
        # TODO: возможно нужно добавить группы и пользователей обладающих Ролью

        query = Entity.query.where((Entity.entity_type == EntityType.POOL) & (Entity.entity_uuid == self.id)).alias()

        # Список администраторов системы
        admins_query = User.query.where(User.is_superuser)
        admins_query_ids = db.select([text('id')]).select_from(admins_query).alias()

        # Список явных пользователей
        users_query = EntityRoleOwner.join(query)
        user_query_ids = db.select([text('user_id')]).select_from(users_query)

        # Список пользователей состоящих в группах
        group_users_query = UserGroup.join(Group).join(EntityRoleOwner.join(query))
        group_users_ids = db.select([text('user_groups.user_id')]).select_from(group_users_query)

        # Список пользователей встречающихся в пересечении
        union_query = union_all(admins_query_ids, user_query_ids, group_users_ids).alias()

        # Формирование заключительного списка пользователей
        finish_query = User.join(union_query, (User.id == text('anon_1.id'))).select().group_by(User.id)
        return await finish_query.gino.all()

    @property
    async def possible_users(self):
        """Пользователи которых можно закрепить за пулом"""
        query = Entity.query.where((Entity.entity_type == EntityType.POOL) & (Entity.entity_uuid == self.id)).alias()

        # Список пользователей состоящих в группах
        group_users_query = UserGroup.join(Group).join(EntityRoleOwner.join(query).alias()).select().alias()
        group_users_ids = db.select([text('anon_7.user_id')]).select_from(group_users_query).alias()

        # Список явных пользователей
        users_query = EntityRoleOwner.join(query).select().alias()
        user_query_ids = db.select([text('anon_4.user_id')]).select_from(users_query).alias()

        # Список администраторов системы
        admins_query = User.query.where(User.is_superuser).alias()
        admins_query_ids = db.select([text('anon_2.id')]).select_from(admins_query).alias()

        # Обьединяем все три запроса и фильтруем активных пользователей
        # Outer join, потому что union_all что-то не взлетел
        union_query = User.join(admins_query_ids, (User.id == text('anon_1.id')), isouter=True).join(user_query_ids, (  # noqa
                User.id == text('anon_3.user_id')), isouter=True).join(group_users_ids,  # noqa
                                                                       (User.id == text('anon_6.user_id')),  # noqa
                                                                       isouter=True).select().where((text('anon_1.id is null') & text('anon_3.user_id is null') & text('anon_6.user_id is null')) & (User.is_active))  # noqa

        return await union_query.gino.load(User).all()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.
    # TODO: избавиться от дублирования

    async def add_user(self, user_id):
        entity = await self.entity_obj
        try:
            async with db.transaction():
                if not entity:
                    entity = await Entity.create(**self.entity)
                ero = await EntityRoleOwner.create(entity_id=entity.id, user_id=user_id)
                user = await User.get(user_id)
                await log.info(_('User {} has been included to pool {}').format(user.username, self.verbose_name))
        except UniqueViolationError:
            raise SimpleError(_('Pool already has permission.'))
        return ero

    async def add_users(self, users_list: list):
        for user_id in users_list:
            await self.add_user(user_id)
        return True

    async def remove_users(self, users_list: list):
        for id in users_list:
            user = await User.get(id)
            await log.info(_('Removing user {} from pool {}').format(user.username, self.verbose_name))
        entity = Entity.select('id').where((Entity.entity_type == self.entity_type) & (Entity.entity_uuid == self.id))
        return await EntityRoleOwner.delete.where(
            (EntityRoleOwner.user_id.in_(users_list)) & (EntityRoleOwner.entity_id == entity)).gino.status()

    async def add_group(self, group_id):
        entity = await self.entity_obj

        try:
            async with db.transaction():
                if not entity:
                    entity = await Entity.create(**self.entity)
                ero = await EntityRoleOwner.create(entity_id=entity.id, group_id=group_id)
                group = await Group.get(group_id)
                await log.info(_('Group {} has been included to pool {}').format(group.verbose_name, self.verbose_name))
        except UniqueViolationError:
            raise SimpleError(_('Pool already has permission.'))
        return ero

    async def add_groups(self, groups_list: list):
        for group_id in groups_list:
            await self.add_group(group_id)
        return True

    async def remove_groups(self, groups_list: list):
        for id in groups_list:
            group = await Group.get(id)
            await log.info(_('Removing group {} from pool {}').format(group.verbose_name, self.verbose_name))
        entity = Entity.select('id').where((Entity.entity_type == self.entity_type) & (Entity.entity_uuid == self.id))
        return await EntityRoleOwner.delete.where(
            (EntityRoleOwner.group_id.in_(groups_list)) & (EntityRoleOwner.entity_id == entity)).gino.status()

    async def add_role(self, role):
        entity = await self.entity_obj

        try:
            async with db.transaction():
                if not entity:
                    entity = await Entity.create(**self.entity)
                ero = await EntityRoleOwner.create(entity_id=entity.id, role=role)
                await log.info(_('Role {} has been set to pool {}.').format(role, self.verbose_name))
        except UniqueViolationError:
            raise SimpleError(_('Pool already has role.'))
        return ero

    async def add_roles(self, roles_list):
        async with db.transaction():
            for role in roles_list:
                await self.add_role(role)

    async def remove_roles(self, roles_list: list):
        role_del = ' '.join(roles_list)
        await log.info(_('Roles: {} was deleted to pool {}').format(role_del, self.verbose_name))
        entity = Entity.select('id').where((Entity.entity_type == self.entity_type) & (Entity.entity_uuid == self.id))
        return await EntityRoleOwner.delete.where(
            (EntityRoleOwner.role.in_(roles_list)) & (EntityRoleOwner.entity_id == entity)).gino.status()

    async def free_assigned_vms(self, users_list: list):
        """
        Будут удалены все записи из EntityRoleOwner соответствующие условию.
        Запрос такой ублюдский, потому что через Join в текущей версии Gino получалось очень много подзапросов.
        :param users_list: uuid пользователей для которых выполняется поиск
        :return: gino.status()
        """

        entity_query = Entity.select('id').where((Entity.entity_type == EntityType.VM) & (
            Entity.entity_uuid.in_(Vm.select('id').where(Vm.pool_id == self.id))))

        ero_query = EntityRoleOwner.delete.where(
            EntityRoleOwner.entity_id.in_(entity_query) & EntityRoleOwner.user_id.in_(users_list))

        return await ero_query.gino.status()

    @classmethod
    async def create(cls, verbose_name, cluster_id, node_id, datapool_id, controller_ip, connection_types):
        controller_id = await Controller.get_controller_id_by_ip(controller_ip)
        if not controller_id:
            raise ValidationError(_('Controller {} not found.').format(controller_ip))

        pool = await super().create(verbose_name=verbose_name, cluster_id=cluster_id, node_id=node_id,
                                    datapool_id=datapool_id,
                                    controller=controller_id,
                                    status=Status.CREATING,
                                    connection_types=connection_types)
        return pool

    async def soft_delete(self, commit=True):
        """Удаление сущности независимо от статуса у которой нет зависимых сущностей"""

        pool_has_vms = await self.has_vms
        if pool_has_vms:
            raise SimpleError(_('Pool has VMs. Please completely remove.'))

        if commit:
            msg = _('Removal pool of desktops {verbose_name} is done.').format(verbose_name=self.verbose_name)
            await self.delete()
            await log.info(msg, entity_dict=self.entity)
        return True

    async def full_delete(self, commit=True):
        """Удаление сущности в статусе ACTIVE с удалением зависимых сущностей"""

        if commit:
            automated_pool = await AutomatedPool.get(self.id)
            # Если пул не автоматический, то удаления не произойдет.
            if automated_pool:
                await automated_pool.remove_vms()

            await self.delete()
            msg = _('Complete removal pool of desktops {verbose_name} is done.').format(verbose_name=self.verbose_name)
            await log.info(msg, entity_dict=self.entity)
        return True

    @classmethod
    async def activate(cls, pool_id):
        pool = await Pool.get(pool_id)
        await pool.update(status=Status.ACTIVE).apply()
        await log.info(_('Pool {} has been activated.').format(pool.verbose_name))
        return True

    @classmethod
    async def deactivate(cls, pool_id):
        pool = await Pool.get(pool_id)
        await pool.update(status=Status.FAILED).apply()
        await log.info(_('Pool {} has been deactivated.').format(pool.verbose_name))
        return True

    @classmethod
    async def enable(cls, pool_id):
        """Отличается от activate тем, что проверяет предыдущий статус."""
        pool = await Pool.get(pool_id)
        # Т.к. сейчас нет возможности остановить создание пула - не трогаем не активные
        if pool.status == Status.FAILED:
            return await pool.activate(pool.id)
        return False

    @classmethod
    async def disable(cls, pool_id):
        """Отличается от deactivate тем, что проверяет предыдущий статус."""
        pool = await Pool.get(pool_id)
        # Т.к. сейчас нет возможности остановить создание пула - не трогаем не активные
        if pool.status == Status.ACTIVE:
            return await pool.deactivate(pool.id)
        return False

    async def get_free_vm(self):
        """Логика такая, что если сущность отсутствует в таблице разрешений - значит никто ей не владеет.
           Требует расширения после расширения модели владения VM"""
        # free_vm_query = Vm.join(Entity, (Vm.id == Entity.entity_uuid)).join(EntityRoleOwner).select().where(
        #     (Entity.entity_type == EntityType.VM) & (Vm.pool_id == self.id) & (text('entity_uuid is null')))
        # log.debug(free_vm_query)
        # return await free_vm_query.gino.load(Vm).first()
        entity_query = Entity.select('entity_uuid').where(
            (Entity.entity_type == EntityType.VM) & (Entity.id.in_(EntityRoleOwner.select('entity_id'))))
        vm_query = Vm.query.where((Vm.pool_id == self.id) & (Vm.broken == False) & (Vm.id.notin_(entity_query)))  # noqa
        return await vm_query.gino.first()

    async def free_user_vms(self, user_id):
        """Т.к. на тонком клиенте нет выбора VM - будут сложности если у пользователя несколько VM в рамках 1 пула."""
        vms_query = Vm.select('id').where(Vm.pool_id == self.id)
        entity_query = Entity.select('id').where(
            (Entity.entity_type == EntityType.VM) & (Entity.entity_uuid.in_(vms_query)))
        ero_query = EntityRoleOwner.delete.where(
            (EntityRoleOwner.user_id == user_id) & (EntityRoleOwner.entity_id.in_(entity_query)))

        return await ero_query.gino.status()


class StaticPool(db.Model):
    """На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах)."""
    __tablename__ = 'static_pool'
    id = db.Column(UUID(), db.ForeignKey('pool.id', ondelete="CASCADE"), primary_key=True, unique=True)

    @property
    def entity_type(self):
        return EntityType.POOL

    @property
    def entity(self):
        return {'entity_type': self.entity_type, 'entity_uuid': self.id}

    @staticmethod
    async def fetch_veil_vm_data(vm_ids: list):
        """Получение информации о VM от контроллера."""
        # TODO: использование кеша ресурсов
        controller_addresses = await Controller.get_addresses()
        # create list of all vms on controllers
        all_vm_veil_data_list = []
        for controller_address in controller_addresses:
            vm_http_client = await VmHttpClient.create(controller_address, '')
            try:
                single_vm_veil_data_list = await vm_http_client.fetch_vms_list()
                # add data about controller address
                for vm_veil_data in single_vm_veil_data_list:
                    vm_veil_data['controller_address'] = controller_address
                all_vm_veil_data_list.extend(single_vm_veil_data_list)
            except (HttpError, OSError) as error_msg:
                await log.error(_('HttpError: {}').format(error_msg))

        # find vm veil data by id
        vm_veil_data_list = []
        for vm_id in vm_ids:
            try:
                data = next(veil_vm_data for veil_vm_data in all_vm_veil_data_list if veil_vm_data['id'] == str(vm_id))
                vm_veil_data_list.append(data)
            except StopIteration:
                raise SimpleError(_('VM with id {} not found in any controllers').format(vm_id))
        return vm_veil_data_list

    @staticmethod
    def vms_on_same_node(node_id: str, veil_vm_data: list) -> bool:
        """Проверка, что все VM находятся на одной Veil node."""
        log.debug(_('StaticPool: Check that all vms are on the same node'))
        # All VMs are on the same node and cluster, all VMs have the same datapool
        # so we can take this data from the first item

        return all(vm_data['node']['id'] == node_id for vm_data in veil_vm_data)

    @classmethod
    async def soft_create(cls, veil_vm_data: list, verbose_name: str,
                          controller_address: str, cluster_id: str, node_id: str,
                          datapool_id: str, connection_types: list):
        """Nested transactions are atomic."""

        async with db.transaction() as tx:  # noqa
            log.debug(_('StaticPool: Create Pool'))
            pl = await Pool.create(verbose_name=verbose_name,
                                   controller_ip=controller_address,
                                   cluster_id=cluster_id,
                                   node_id=node_id,
                                   datapool_id=datapool_id,
                                   connection_types=connection_types)

            log.debug(_('StaticPool: Create StaticPool'))
            pool = await super().create(id=pl.id)

            log.debug(_('StaticPool: Create VMs'))
            for vm_info in veil_vm_data:
                log.debug(_('VM info {}').format(vm_info))
                await Vm.create(id=vm_info['id'],
                                verbose_name=vm_info['verbose_name'],
                                pool_id=pool.id,
                                template_id=None,
                                created_by_vdi=False)
                log.debug(_('VM {} created.').format(vm_info['verbose_name']))

            await log.info(_('Static pool {} created.').format(verbose_name))
            await pool.activate()

            return pool

    @classmethod
    async def soft_update(cls, pool_id, verbose_name, keep_vms_on, connection_types):
        async with db.transaction() as tx:  # noqa
            if verbose_name:
                await Pool.update.values(verbose_name=verbose_name).where(Pool.id == pool_id).gino.status()
            if keep_vms_on is not None:
                await Pool.update.values(keep_vms_on=keep_vms_on).where(Pool.id == pool_id).gino.status()
            if connection_types is not None and connection_types:
                await Pool.update.values(connection_types=connection_types).where(Pool.id == pool_id).gino.status()
            msg = _('Static pool {} is updated.').format(verbose_name)
            description = '{} {} {}'.format(verbose_name, keep_vms_on, connection_types)
            await log.info(msg, description=description)
        return True

    async def activate(self):
        return await Pool.activate(self.id)

    async def deactivate(self):
        return await Pool.deactivate(self.id)


class AutomatedPool(db.Model):
    """
    reserve_size - желаемое минимальное количество подогретых машин (добавленных в пул, но не имеющих пользователя)
    На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах).
    """

    __tablename__ = 'automated_pool'

    id = db.Column(UUID(), db.ForeignKey('pool.id', ondelete="CASCADE"), primary_key=True, unique=True)
    template_id = db.Column(UUID(), nullable=False)

    # Pool size settings
    min_size = db.Column(db.Integer(), nullable=False, default=1)
    max_size = db.Column(db.Integer(), nullable=False, default=200)
    max_vm_amount = db.Column(db.Integer(), nullable=False, default=1000)
    increase_step = db.Column(db.Integer(), nullable=False, default=3)
    min_free_vms_amount = db.Column(db.Integer(), nullable=False, default=3)
    max_amount_of_create_attempts = db.Column(db.Integer(), nullable=False, default=2)

    initial_size = db.Column(db.Integer(), nullable=False, default=1)
    reserve_size = db.Column(db.Integer(), nullable=False, default=0)
    total_size = db.Column(db.Integer(), nullable=False, default=1)  # Размер пула
    vm_name_template = db.Column(db.Unicode(length=100), nullable=True)
    os_type = db.Column(db.Unicode(length=100), nullable=True)

    create_thin_clones = db.Column(db.Boolean(), nullable=False, default=True)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties:

    @property
    def entity_type(self):
        return EntityType.POOL

    @property
    def entity(self):
        return {'entity_type': self.entity_type, 'entity_uuid': self.id}

    @property
    async def verbose_name(self):
        pool = await Pool.get(self.id)
        if pool:
            return pool.verbose_name

    @property
    async def node_id(self):
        pool = await Pool.get(self.id)
        if pool:
            return pool.node_id

    @property
    async def datapool_id(self):
        pool = await Pool.get(self.id)
        if pool:
            return pool.datapool_id

    @property
    async def controller_ip(self):
        return await Pool.get_controller_ip(self.id)

    @property
    async def keep_vms_on(self):
        pool = await Pool.get(self.id)
        if pool:
            return pool.keep_vms_on

    # ----- ----- ----- ----- ----- ----- -----

    async def activate(self):
        return await Pool.activate(self.id)

    async def deactivate(self):
        return await Pool.deactivate(self.id)

    @classmethod
    async def soft_create(cls, verbose_name, controller_ip, cluster_id, node_id,
                          template_id, datapool_id, min_size, max_size, max_vm_amount, increase_step,
                          min_free_vms_amount,
                          max_amount_of_create_attempts, initial_size, reserve_size, total_size, vm_name_template,
                          create_thin_clones, connection_types):
        """Nested transactions are atomic."""
        async with db.transaction() as tx:  # noqa
            # Create Pool
            log.debug(_('Create Pool {}').format(verbose_name))
            pool = await Pool.create(verbose_name=verbose_name,
                                     cluster_id=cluster_id,
                                     node_id=node_id,
                                     datapool_id=datapool_id,
                                     controller_ip=controller_ip,
                                     connection_types=connection_types)

            log.debug(_('Create AutomatedPool {}').format(verbose_name))
            # Create AutomatedPool
            automated_pool = await super().create(id=pool.id,
                                                  template_id=template_id,
                                                  min_size=min_size,
                                                  max_size=max_size,
                                                  max_vm_amount=max_vm_amount,
                                                  increase_step=increase_step,
                                                  min_free_vms_amount=min_free_vms_amount,
                                                  max_amount_of_create_attempts=max_amount_of_create_attempts,
                                                  initial_size=initial_size,
                                                  reserve_size=reserve_size,
                                                  total_size=total_size,
                                                  vm_name_template=vm_name_template,
                                                  create_thin_clones=create_thin_clones)

            await log.info(_('AutomatedPool {} is created').format(verbose_name))

            return automated_pool

    async def soft_update(self, verbose_name, reserve_size, total_size, vm_name_template, keep_vms_on: bool,
                          create_thin_clones: bool, connection_types):
        pool_kwargs = dict()
        auto_pool_kwargs = dict()

        async with db.transaction() as tx:  # noqa
            # Update Pool values
            if verbose_name:
                pool_kwargs['verbose_name'] = verbose_name
            if isinstance(keep_vms_on, bool):
                pool_kwargs['keep_vms_on'] = keep_vms_on
            if connection_types:
                pool_kwargs['connection_types'] = connection_types

            if pool_kwargs:
                log.debug(_('Update Pool values for AutomatedPool {}').format(await self.verbose_name))
                pool = await Pool.get(self.id)
                await pool.update(**pool_kwargs).apply()

            # Update AutomatedPool values
            if reserve_size:
                auto_pool_kwargs['reserve_size'] = reserve_size
            if total_size:
                auto_pool_kwargs['total_size'] = total_size
            if vm_name_template:
                auto_pool_kwargs['vm_name_template'] = vm_name_template
            if isinstance(create_thin_clones, bool):
                auto_pool_kwargs['create_thin_clones'] = create_thin_clones
            if auto_pool_kwargs:
                descr = str(auto_pool_kwargs)
                await log.info(_('Update AutomatedPool values for {}').format(await self.verbose_name), description=descr)
                await self.update(**auto_pool_kwargs).apply()

        automated_pool = await self.get(self.id)
        msg = _('Automated pool {name} updated.').format(name=await automated_pool.verbose_name)
        log.debug(msg)

        return True

    async def add_vm(self, domain_index):
        """
        Try to add VM to pool
        :param domain_index:
        :return:
        """

        vm_name_template = self.vm_name_template or await self.verbose_name
        verbose_name = '{}-{}'.format(vm_name_template, domain_index)
        controller_address = await self.controller_ip
        params = {
            'verbose_name': verbose_name,
            'domain_id': str(self.template_id),
            'datapool_id': str(await self.datapool_id),
            'controller_ip': controller_address,
            'node_id': str(await self.node_id),
            'create_thin_clones': self.create_thin_clones,
            'domain_index': domain_index
        }

        for i in range(self.max_amount_of_create_attempts):
            log.debug(_('add_domain {}, attempt № {}, of {}').format(verbose_name, i, self.max_amount_of_create_attempts))
            try:
                vm_info = await Vm.copy(**params)
                current_vm_task_id = vm_info['task_id']
                log.debug(_('VM creation task id: {}').format(current_vm_task_id))
            except HttpError as http_error:
                # Обработка BadRequest происходит в Vm.copy()
                await log.error(http_error)
                log.debug(_('Fail to create VM on ECP. Re-run.'))
                await asyncio.sleep(1)
                continue

            # Мониторим все таски на ECP и ищем там нашу. Такое себе.

            log.debug(_('Subscribe to ws messages.'))
            response_waiter = WaiterSubscriptionObserver()
            response_waiter.add_subscription_source('/tasks/')

            resources_monitor_manager.subscribe(response_waiter)
            log.debug(_('Wait for result.'))

            def _is_vm_creation_task(name):
                """
                Determine domain creation task by name
                """
                if name.startswith(_('Create virtual machine')):
                    return True
                if all(word in name.lower() for word in ['creating', 'virtual', 'machine']):
                    return True
                return False

            def _check_if_vm_created(json_message):
                try:
                    obj = json_message['object']

                    if _is_vm_creation_task(obj['name']) and current_vm_task_id == obj['parent']:
                        if obj['status'] == 'SUCCESS':
                            return True
                except KeyError:
                    pass
                return False

            async def check_task_status(task_id):
                token = await Controller.get_token(controller_address)
                veil_client = VeilHttpClient(controller_address, token=token)
                return await veil_client.check_task_status(task_id)

            async def check_vm_status(vm_id):
                vm_client = await VmHttpClient.create(controller_address, vm_id)
                return await vm_client.check_status()

            is_vm_successfully_created = await response_waiter.wait_for_message(
                _check_if_vm_created, VEIL_WS_MAX_TIME_TO_WAIT)

            resources_monitor_manager.unsubscribe(response_waiter)

            if not is_vm_successfully_created:
                log.debug(
                    _('Could not get the response about result of creation VM on ECP by WS. Task status check.'))
                is_vm_successfully_created = await check_task_status(task_id=current_vm_task_id)

            if not is_vm_successfully_created:
                log.debug(_('Probably task is not done. Check VM status.'))
                is_vm_successfully_created = await check_vm_status(vm_info['id'])

            # Эксперементальная обнова. VM создается в любом случае, но если что-то пошло не так, то мы создаем ее в БД.
            # if is_vm_successfully_created:
            #     await Vm.create(id=vm_info['id'],
            #                     pool_id=str(self.id),
            #                     template_id=str(self.template_id),
            #                     created_by_vdi=True,
            #                     verbose_name=vm_info['verbose_name'])
            #     return vm_info
            #
            # log.debug('Fail to create VM on ECP. Re-run.')
            # await asyncio.sleep(1)
            # continue
            vm_is_broken = False if is_vm_successfully_created else False
            await Vm.create(id=vm_info['id'],
                            pool_id=str(self.id),
                            template_id=str(self.template_id),
                            created_by_vdi=True,
                            verbose_name=vm_info['verbose_name'],
                            broken=vm_is_broken)

            await log.info(_('VM {} is added to Automated pool {}').format(vm_info['verbose_name'], self.verbose_name))

            return vm_info

        raise VmCreationError(
            _('Error with create VM {} was {} times.').format(verbose_name, self.max_amount_of_create_attempts))

    async def add_initial_vms(self):
        """Create required initial amount of VMs for auto pool
           Основная логика сохранена со старой схемы. На рефакторинг внутреннего кода нет времени.
           Главное, что бы хотелось тут и в других местах создания виртуалок - отправлять диапазоны виртуалок
        """

        # Fetching template info from controller.
        controller_address = await self.controller_ip
        verbose_name = await self.verbose_name

        log.debug(_('Add {} initial vms for pool {}. Controller address: {}').format(self.initial_size,
                                                                                     verbose_name,
                                                                                     controller_address))

        pool_os_type = await Vm.get_template_os_type(controller_address=controller_address,
                                                     template_id=self.template_id)

        log.debug(_('Pool {} os type is: {}').format(verbose_name, pool_os_type))
        await self.update(os_type=pool_os_type).apply()

        await log.info(_('Automated pool creation started'), entity_dict=self.entity)

        vm_list = list()
        vm_index = 1

        try:
            for i in range(self.initial_size):
                vm = await self.add_vm(vm_index)
                vm_index = vm['domain_index'] + 1
                vm_list.append(vm)

                msg = _('Automated pool creation. Created {} VMs from {}').format(i + 1, self.initial_size)
                await log.info(msg, entity_dict=self.entity)

                # notify VDI front about progress(WS)
                msg_dict = dict(msg=msg,
                                mgs_type='data',
                                event='pool_creation_progress',
                                pool_id=str(self.id),
                                domain_index=vm_index,
                                domain_verbose_name=vm['verbose_name'],
                                initial_size=self.initial_size,
                                resource=VDI_TASKS_SUBSCRIPTION)

                internal_event_monitor.signal_event(msg_dict)

        except VmCreationError as vm_error:
            # log that we cant create required initial amount of VMs
            await log.error(msg=_('Can\'t create VM'), description=str(vm_error))

        # notify VDI front about pool creation result (WS)
        is_creation_successful = (len(vm_list) == self.initial_size)

        if is_creation_successful:
            msg = _('Automated pool successfully created. Initial VM amount {}').format(len(vm_list))
            await log.info(msg, entity_dict=self.entity)
        else:
            msg = _('Automated pool created with errors. VMs created: {}. Required: {}').format(len(vm_list),
                                                                                                self.initial_size)
            await log.error(msg, entity_dict=self.entity)

        msg_dict = dict(msg=msg,
                        msg_type='data',
                        event='pool_creation_completed',
                        pool_id=str(self.id),
                        amount_of_created_vms=len(vm_list),
                        initial_size=self.initial_size,
                        is_successful=is_creation_successful,
                        resource=VDI_TASKS_SUBSCRIPTION)

        internal_event_monitor.signal_event(msg_dict)

        # Пробросить исключение, если споткнулись на создании машин
        if not is_creation_successful:
            raise PoolCreationError(_('Could not create the required number of machines.'))

    async def init_pool(self):
        """Создание на пуле виртуальных машин по параметрам пула."""

        # locks
        async with pool_task_manager.get_pool_lock(str(self.id)).lock:
            async with pool_task_manager.get_template_lock(str(self.template_id)).lock:
                try:
                    await self.add_initial_vms()
                except PoolCreationError as E:
                    await log.error('{exception}'.format(exception=str(E)))
                    await self.deactivate()
                else:
                    await self.activate()

    async def expand_pool(self):
        """
        Корутина расширения автом. пула
        Check and expand pool if required
        :return:
        """
        async with pool_task_manager.get_pool_lock(str(self.id)).lock:
            async with pool_task_manager.get_template_lock(str(self.template_id)).lock:
                # TODO: код перенесен, чтобы работал. Принципиально не перерабатывался.
                # Check that total_size is not reached
                pool = await Pool.get(self.id)
                vm_amount_in_pool = await pool.get_vm_amount()

                # If reached then do nothing
                if vm_amount_in_pool >= self.total_size:
                    return

                # Число машин в пуле, неимеющих пользователя
                free_vm_amount = await pool.get_vm_amount(only_free=True)

                # Если подогретых машин слишком мало, то пробуем добавить еще
                # Условие расширения изменено. Первое условие было < - тестируем.
                if free_vm_amount <= self.reserve_size and free_vm_amount <= self.min_free_vms_amount:
                    # Max possible amount of VMs which we can add to the pool
                    max_possible_amount_to_add = self.total_size - vm_amount_in_pool
                    # Real amount that we can add to the pool
                    real_amount_to_add = min(max_possible_amount_to_add, self.increase_step)
                    # add VMs.
                    try:
                        for i in range(0, real_amount_to_add):
                            domain_index = vm_amount_in_pool + i
                            await self.add_vm(domain_index)
                    except VmCreationError as vm_error:
                        await log.error(_('VM creating error:'))
                        log.debug(vm_error)

    async def remove_vms(self):
        """Интерфейс для запуска команды HttpClient на удаление виртуалки"""

        log.debug(_('Delete VMs for AutomatedPool {}').format(await self.verbose_name))
        vms = await Vm.query.where(Vm.pool_id == self.id).gino.all()
        for vm in vms:
            log.debug(_('Calling soft delete for vm {}').format(vm.verbose_name))
            await vm.soft_delete()
        return True
