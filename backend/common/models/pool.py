# -*- coding: utf-8 -*-
import asyncio
import json
import uuid
from enum import Enum
from sqlalchemy import and_, union_all, case, literal_column, desc, text, Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from asyncpg.exceptions import UniqueViolationError

from common.settings import (VEIL_WS_MAX_TIME_TO_WAIT,
                             POOL_MAX_SIZE, POOL_MIN_SIZE, POOL_MAX_CREATE_ATTEMPTS, POOL_MAX_VM_AMOUNT)
from common.database import db
from common.veil.veil_gino import Status, EntityType, VeilModel
from common.veil.veil_errors import VmCreationError, PoolCreationError, SimpleError, ValidationError
from common.utils import extract_ordering_data
from web_app.auth.license.utils import License
from common.veil.veil_redis import (get_thin_clients_count, REDIS_CLIENT, INTERNAL_EVENTS_CHANNEL,
                                    a_redis_wait_for_message, WS_MONITOR_CHANNEL_OUT)
from web_app.front_ws_api.subscription_sources import VDI_TASKS_SUBSCRIPTION

from common.models.auth import (User as UserModel, Entity as EntityModel, EntityRoleOwner as EntityRoleOwnerModel,
                                Group as GroupModel, UserGroup as UserGroupModel)
from common.models.vm import Vm as VmModel

from common.languages import lang_init
from common.log.journal import system_logger

_ = lang_init()


class Pool(VeilModel):
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

    POOL_TYPE_LABEL = 'pool_type'
    EXTRA_ORDER_FIELDS = ['controller_address', 'users_count', 'vm_amount', 'pool_type']

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
    # Properties and getters:

    @property
    def id_str(self):
        return str(self.id)

    @property
    async def possible_connection_types(self):
        return [connection_type for connection_type in self.PoolConnectionTypes if
                connection_type not in self.connection_types]

    @property
    def entity_type(self):
        return EntityType.POOL

    @property
    async def controller_obj(self):
        from common.models.controller import Controller
        return await Controller.get(self.controller)

    @property
    async def has_vms(self):
        """Проверяем наличие виртуальных машин"""
        # from common.models import VmModel
        vm_count = await db.select([db.func.count(VmModel.id)]).where(
            VmModel.pool_id == self.id).gino.scalar()
        if vm_count == 0:
            return False
        return True

    @property
    async def vms(self):
        """Возвращаем виртуальные машины привязанные к пулу."""
        return await VmModel.query.where(VmModel.pool_id == self.id).gino.all()

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
        from common.models.controller import Controller

        if not ordering or not isinstance(ordering, str):
            return query

        # Определяем порядок сортировки по наличию "-" вначале строки
        (ordering, reversed_order) = extract_ordering_data(ordering)

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
                    vms_count = db.func.count(VmModel.id)
                    query = query.order_by(desc(vms_count)) if reversed_order else query.order_by(vms_count)
                elif ordering == 'pool_type':
                    query = query.order_by(desc(text(Pool.POOL_TYPE_LABEL))) if reversed_order else query.order_by(
                        text(Pool.POOL_TYPE_LABEL))
            else:
                # Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order
                query = query.order_by(desc(getattr(Pool, ordering))) if reversed_order else query.order_by(
                    getattr(Pool, ordering))
        except AttributeError:
            entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
            raise SimpleError(_('Incorrect sorting option {}.').format(ordering), entity=entity)
        return query

    @staticmethod
    def get_pools_query(ordering=None, user_id=None, groups_ids_list=None, role_set=None):
        from common.models.controller import Controller

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
                permissions_query = EntityModel.join(EntityRoleOwnerModel.query.where(
                    (EntityRoleOwnerModel.user_id == user_id) | (EntityRoleOwnerModel.role.in_(role_set)) | (
                        EntityRoleOwnerModel.group_id.in_(groups_ids_list))).alias())
            else:
                permission_outer = True
                permissions_query = EntityModel.join(EntityRoleOwnerModel)

            query = query.select_from(
                Pool.join(AutomatedPool, isouter=True).join(Controller, isouter=True).join(VmModel, isouter=True).join(
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
    async def get_pools(limit, offset, filters=None, ordering=None):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        # TODO: проверить используется ли. Заменить на Pool.get?
        query = Pool.get_pools_query(ordering=ordering)
        if filters:
            query = query.where(and_(*filters))
        return await query.limit(limit).offset(offset).gino.all()

    @staticmethod
    async def get_controller_ip(pool_id):
        # TODO: заменить на property controller_address
        from common.models.controller import Controller as ControllerModel
        query = db.select([ControllerModel.address]).select_from(ControllerModel.join(Pool)).where(
            Pool.id == pool_id)
        return await query.gino.scalar()

    async def get_vm_amount(self, only_free=False):
        """
        Нужно дорабатывать - отказаться от in и дублирования кода.
        :param only_free: учитываем только свободные VM
        :return: int
        """
        # from common.models import VmModel
        if only_free:
            entity_query = EntityModel.select('entity_uuid').where(
                (EntityModel.entity_type == EntityType.VM) & (
                    EntityModel.id.in_(EntityRoleOwnerModel.select('id').where(EntityRoleOwnerModel.user_id != None))))  # noqa

            vm_query = db.select([db.func.count(VmModel.id)]).where(
                (VmModel.pool_id == self.id) & (VmModel.id.notin_(entity_query))).group_by(VmModel.id)

            return await vm_query.gino.scalar()

        return await db.select([db.func.count()]).where(VmModel.pool_id == self.id).gino.scalar()

    async def get_vm(self, user_id):
        """Возвращает ВМ пользователя с учетом его прав.

        Сочитание pool id и username уникальное, т.к. пользователь не может иметь больше одной машины в пуле.
        """
        # from common.models import VmModel
        assigned_users = await self.assigned_users
        if user_id not in [user[0] for user in assigned_users]:
            return
        entity_query = EntityModel.select('entity_uuid').where(
            (EntityModel.entity_type == EntityType.VM) & (
                EntityModel.id.in_(EntityRoleOwnerModel.select('entity_id').where(EntityRoleOwnerModel.user_id == user_id))))
        vm_query = VmModel.query.where((VmModel.id.in_(entity_query)) & (VmModel.pool_id == self.id))
        return await vm_query.gino.first()

    @property
    async def roles(self):
        """Уникальные роли назначенные пулу (без учета групп и пользователей)."""
        query = EntityModel.query.where((EntityModel.entity_type == EntityType.POOL) & (EntityModel.entity_uuid == self.id)).alias()
        filtered_query = EntityRoleOwnerModel.join(query).select().alias()
        result_query = db.select([text('anon_1.role')]).select_from(filtered_query).group_by('role')
        return await result_query.gino.all()

    @property
    def assigned_groups_query(self):
        """Группы назначенные пулу"""
        # TODO: возможно нужно добавить группы и пользователей обладающих Ролью
        query = EntityModel.query.where((EntityModel.entity_type == EntityType.POOL) & (EntityModel.entity_uuid == self.id)).alias()
        return GroupModel.join(EntityRoleOwnerModel.join(query).alias()).select()

    @property
    async def assigned_groups(self):
        return await self.assigned_groups_query.gino.load(GroupModel).all()

    async def assigned_groups_paginator(self, limit, offset):
        return await self.assigned_groups_query.limit(limit).offset(offset).gino.load(GroupModel).all()

    @property
    async def possible_groups(self):
        query = EntityModel.query.where((EntityModel.entity_type == EntityType.POOL) & (EntityModel.entity_uuid == self.id)).alias()
        filtered_query = GroupModel.join(EntityRoleOwnerModel.join(query).alias(), isouter=True).select().where(text('anon_1.entity_role_owner_group_id is null'))  # noqa
        return await filtered_query.order_by(GroupModel.verbose_name).gino.load(GroupModel).all()

    @property
    async def assigned_users(self):
        """Пользователи назначенные пулу (с учетом групп)"""
        # TODO: возможно нужно добавить группы и пользователей обладающих Ролью

        query = EntityModel.query.where((EntityModel.entity_type == EntityType.POOL) & (EntityModel.entity_uuid == self.id)).alias()

        # Список администраторов системы
        admins_query = UserModel.query.where(UserModel.is_superuser)
        admins_query_ids = db.select([text('id')]).select_from(admins_query).alias()

        # Список явных пользователей
        users_query = EntityRoleOwnerModel.join(query)
        user_query_ids = db.select([text('user_id')]).select_from(users_query)

        # Список пользователей состоящих в группах
        group_users_query = UserGroupModel.join(GroupModel).join(EntityRoleOwnerModel.join(query))
        group_users_ids = db.select([text('user_groups.user_id')]).select_from(group_users_query)

        # Список пользователей встречающихся в пересечении
        union_query = union_all(admins_query_ids, user_query_ids, group_users_ids).alias()

        # Формирование заключительного списка пользователей
        finish_query = UserModel.join(union_query, (UserModel.id == text('anon_1.id'))).select().group_by(UserModel.id)
        return await finish_query.gino.all()

    @property
    async def possible_users(self):
        """Пользователи которых можно закрепить за пулом"""
        query = EntityModel.query.where((EntityModel.entity_type == EntityType.POOL) & (EntityModel.entity_uuid == self.id)).alias()

        # Список пользователей состоящих в группах
        group_users_query = UserGroupModel.join(GroupModel).join(EntityRoleOwnerModel.join(query).alias()).select().alias()
        group_users_ids = db.select([text('anon_7.user_id')]).select_from(group_users_query).alias()

        # Список явных пользователей
        users_query = EntityRoleOwnerModel.join(query).select().alias()
        user_query_ids = db.select([text('anon_4.user_id')]).select_from(users_query).alias()

        # Список администраторов системы
        admins_query = UserModel.query.where(UserModel.is_superuser).alias()
        admins_query_ids = db.select([text('anon_2.id')]).select_from(admins_query).alias()

        # Обьединяем все три запроса и фильтруем активных пользователей
        # Outer join, потому что union_all что-то не взлетел
        union_query = UserModel.join(admins_query_ids, (UserModel.id == text('anon_1.id')), isouter=True).join(user_query_ids, (  # noqa
                UserModel.id == text('anon_3.user_id')), isouter=True).join(group_users_ids,  # noqa
                                                                       (UserModel.id == text('anon_6.user_id')),  # noqa
                                                                       isouter=True).select().where((text('anon_1.id is null') & text('anon_3.user_id is null') & text('anon_6.user_id is null')) & (UserModel.is_active))  # noqa

        return await union_query.order_by(UserModel.username).gino.load(UserModel).all()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.
    # TODO: избавиться от дублирования

    async def add_user(self, user_id, creator):
        entity = await self.entity_obj
        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityRoleOwnerModel.create(entity_id=entity.id, user_id=user_id)
                user = await UserModel.get(user_id)
                await system_logger.info(
                    _('User {} has been included to pool {}').format(user.username, self.verbose_name),
                    user=creator,
                    entity=self.entity)
        except UniqueViolationError:
            raise SimpleError(_('{} already has permission.').format(type(self).__name__), user=creator, entity=self.entity)
        return ero

    async def remove_users(self, creator, users_list: list):
        for user_id in users_list:
            user = await UserModel.get(user_id)
            await system_logger.info(_('Removing user {} from pool {}').format(user.username, self.verbose_name),
                                     user=creator,
                                     entity=self.entity)
        entity = EntityModel.select('id').where((EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id))
        return await EntityRoleOwnerModel.delete.where(
            (EntityRoleOwnerModel.user_id.in_(users_list)) & (EntityRoleOwnerModel.entity_id == entity)).gino.status()

    async def add_group(self, group_id, creator):
        entity = await self.entity_obj

        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityRoleOwnerModel.create(entity_id=entity.id, group_id=group_id)
                group = await GroupModel.get(group_id)
                await system_logger.info(
                    _('Group {} has been included to pool {}').format(group.verbose_name, self.verbose_name),
                    user=creator,
                    entity=self.entity)
        except UniqueViolationError:
            raise SimpleError(_('Pool already has permission.'), user=creator, entity=self.entity)
        return ero

    async def add_groups(self, creator, groups_list: list):
        for group_id in groups_list:
            await self.add_group(group_id, creator)
        return True

    async def remove_groups(self, creator, groups_list: list):
        for group_id in groups_list:
            group = await GroupModel.get(group_id)
            await system_logger.info(_('Removing group {} from pool {}').format(group.verbose_name, self.verbose_name),
                                     user=creator,
                                     entity=self.entity
                                     )
        entity = EntityModel.select('id').where((EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id))
        return await EntityRoleOwnerModel.delete.where(
            (EntityRoleOwnerModel.group_id.in_(groups_list)) & (EntityRoleOwnerModel.entity_id == entity)).gino.status()

    async def add_role(self, role, creator):
        entity = await self.entity_obj

        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityRoleOwnerModel.create(entity_id=entity.id, role=role)
                await system_logger.info(_('Role {} has been set to pool {}.').format(role, self.verbose_name),
                                         user=creator,
                                         entity=self.entity)
        except UniqueViolationError:
            raise SimpleError(_('Pool already has role.'), user=creator, entity=self.entity)
        return ero

    async def remove_roles(self, creator, roles_list: list):
        role_del = ' '.join(roles_list)
        await system_logger.info(_('Roles: {} was deleted to pool {}').format(role_del, self.verbose_name),
                                 user=creator,
                                 entity=self.entity)
        entity = EntityModel.select('id').where(
            (EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id))
        return await EntityRoleOwnerModel.delete.where(
            (EntityRoleOwnerModel.role.in_(roles_list)) & (EntityRoleOwnerModel.entity_id == entity)).gino.status()

    async def free_assigned_vms(self, users_list: list):
        """
        Будут удалены все записи из EntityRoleOwner соответствующие условию.
        Запрос такой ублюдский, потому что через Join в текущей версии Gino получалось очень много подзапросов.
        :param users_list: uuid пользователей для которых выполняется поиск
        :return: gino.status()
        """
        # from common.models import VmModel
        entity_query = EntityModel.select('id').where((EntityModel.entity_type == EntityType.VM) & (
            EntityModel.entity_uuid.in_(VmModel.select('id').where(VmModel.pool_id == self.id))))

        ero_query = EntityRoleOwnerModel.delete.where(
            EntityRoleOwnerModel.entity_id.in_(entity_query) & EntityRoleOwnerModel.user_id.in_(users_list))

        return await ero_query.gino.status()

    @classmethod
    async def create(cls, verbose_name, cluster_id, node_id, datapool_id, controller_ip, connection_types):
        # TODO: controller_ip заменить на controller_id
        from common.models.controller import Controller
        controller_id = await Controller.get_controller_id_by_ip(controller_ip)
        if not controller_id:
            raise ValidationError(_('Controller {} not found.').format(controller_ip))

        pool = await super().create(verbose_name=verbose_name, cluster_id=cluster_id, node_id=node_id,
                                    datapool_id=datapool_id,
                                    controller=controller_id,
                                    status=Status.CREATING,
                                    connection_types=connection_types)
        return pool

    async def full_delete(self, creator, commit=True):
        """Удаление сущности с удалением зависимых сущностей"""
        if commit:
            automated_pool = await AutomatedPool.get(self.id)

            if automated_pool:
                await automated_pool.remove_vms(creator=creator)
            await self.delete()
            msg = _('Complete removal pool of desktops {verbose_name} is done.').format(verbose_name=self.verbose_name)
            await system_logger.info(msg, entity=self.entity, user=creator)
        return True

    @staticmethod
    async def delete_pool(pool, creator, full=False):
        if full:
            status = await pool.full_delete(creator)
        else:
            """Удаление сущности независимо от статуса у которой нет зависимых сущностей"""
            pool_has_vms = await Pool.has_vms
            if pool_has_vms:
                raise SimpleError(_('Pool has VMs. Please completely remove.'), user=creator)
            status = await pool.soft_delete(creator=creator)

        return status

    @classmethod
    async def activate(cls, pool_id):
        pool = await Pool.get(pool_id)
        await pool.update(status=Status.ACTIVE).apply()
        entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
        await system_logger.info(_('Pool {} has been activated.').format(pool.verbose_name), entity=entity)
        return True

    @classmethod
    async def deactivate(cls, pool_id):
        pool = await Pool.get(pool_id)
        await pool.update(status=Status.FAILED).apply()
        entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
        await system_logger.info(_('Pool {} has been deactivated.').format(pool.verbose_name), entity=entity)
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
        # free_vm_query = VmModel.join(Entity, (VmModel.id == EntityModel.entity_uuid)).join(EntityRoleOwner).select().where(
        #     (EntityModel.entity_type == EntityType.VM) & (VmModel.pool_id == self.id) & (text('entity_uuid is null')))
        # await system_logger.debug(free_vm_query)
        # return await free_vm_query.gino.load(VmModel..first()
        entity_query = EntityModel.select('entity_uuid').where(
            (EntityModel.entity_type == EntityType.VM) & (EntityModel.id.in_(EntityRoleOwnerModel.select('entity_id'))))
        vm_query = VmModel.query.where((VmModel.pool_id == self.id) & (VmModel.broken == False) & (VmModel.id.notin_(entity_query)))  # noqa
        return await vm_query.gino.first()

    async def free_user_vms(self, user_id):
        """Т.к. на тонком клиенте нет выбора VM - будут сложности если у пользователя несколько VM в рамках 1 пула."""
        # from common.models import VmModel
        vms_query = VmModel.select('id').where(VmModel.pool_id == self.id)
        entity_query = EntityModel.select('id').where(
            (EntityModel.entity_type == EntityType.VM) & (EntityModel.entity_uuid.in_(vms_query)))
        ero_query = EntityRoleOwnerModel.delete.where(
            (EntityRoleOwnerModel.user_id == user_id) & (EntityRoleOwnerModel.entity_id.in_(entity_query)))

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

    # @staticmethod
    # async def fetch_veil_vm_data(vm_ids: list):
    #     """Получение информации о VM от контроллера."""
    #     # TODO: использование кеша ресурсов
    #     controller_addresses = await controller_module.ControllerModel.odel.get_addresses()
    #     # create list of all vms on controllers
    #     all_vm_veil_data_list = []
    #     controllers = await controller_module.ControllerModel.odel.objects.gino.all()
    #     for controller in controllers:
    #
    #
    #
    #     for controller_address in controller_addresses:
    #         vm_http_client = await VmModel.ttpClient.create(controller_address, '')
    #         try:
    #             single_vm_veil_data_list = await vm_http_client.fetch_vms_list()
    #             # add data about controller address
    #             for vm_veil_data in single_vm_veil_data_list:
    #                 vm_veil_data['controller_address'] = controller_address
    #             all_vm_veil_data_list.extend(single_vm_veil_data_list)
    #         except (HttpError, OSError) as error_msg:
    #             entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
    #             await system_logger.error(_('HttpError: {}').format(error_msg), entity=entity)
    #
    #     # find vm veil data by id
    #     vm_veil_data_list = []
    #     for vm_id in vm_ids:
    #         try:
    #             data = next(veil_vm_data for veil_vm_data in all_vm_veil_data_list if veil_vm_data['id'] == str(vm_id))
    #             vm_veil_data_list.append(data)
    #         except StopIteration:
    #             entity = {'entity_type': EntityType.POOL, 'entity_uuid': None}
    #             raise SimpleError(_('VM with id {} not found in any controllers').format(vm_id), entity=entity)
    #     return vm_veil_data_list

    @staticmethod
    def vms_on_same_node(node_id: str, veil_vm_data: list) -> bool:
        """Проверка, что все VM находятся на одной Veil node."""
        system_logger._debug('StaticPool: Check that all vms are on the same node')
        # All VMs are on the same node and cluster, all VMs have the same datapool
        # so we can take this data from the first item

        return all(vm_data['node']['id'] == node_id for vm_data in veil_vm_data)

    @classmethod
    async def soft_create(cls, creator, veil_vm_data: list, verbose_name: str,
                          controller_address: str, cluster_id: str, node_id: str,
                          datapool_id: str, connection_types: list):
        """Nested transactions are atomic."""
        # from common.models import VmModel
        async with db.transaction() as tx:  # noqa
            await system_logger.debug(_('StaticPool: Create Pool'))
            pl = await Pool.create(verbose_name=verbose_name,
                                   controller_ip=controller_address,
                                   cluster_id=cluster_id,
                                   node_id=node_id,
                                   datapool_id=datapool_id,
                                   connection_types=connection_types)

            await system_logger.debug(_('StaticPool: Create StaticPool'))
            pool = await super().create(id=pl.id)

            await system_logger.debug(_('StaticPool: Create VMs'))
            # TODO: эксперементальное обновление
            for vm_type in veil_vm_data:
                await VmModel.create(id=vm_type.id,
                                     verbose_name=vm_type.verbose_name,
                                     pool_id=pool.id,
                                     template_id=None,
                                     created_by_vdi=False)
                await system_logger.debug(_('VM {} created.').format(vm_type.verbose_name))

            await system_logger.info(_('Static pool {} created.').format(verbose_name), user=creator, entity=pool.entity)
            await pool.activate()
        return pool

    @classmethod
    async def soft_update(cls, id, verbose_name, keep_vms_on, connection_types, creator):
        async with db.transaction() as tx:  # noqa
            update_type, update_dict = await Pool.soft_update(id, verbose_name=verbose_name,
                                                              keep_vms_on=keep_vms_on,
                                                              connection_types=connection_types,
                                                              creator=creator
                                                              )

            msg = _('Static pool {} is updated.').format(update_type.verbose_name)
            creator = update_dict.pop('creator')
            desc = str(update_dict)
            await system_logger.info(msg, description=desc, user=creator, entity=update_type.entity)
        return True

    async def activate(self):
        return await Pool.activate(self.id)

    async def deactivate(self):
        return await Pool.deactivate(self.id)


class AutomatedPool(db.Model):
    """Модель описывающая автоматический (динамический) пул.

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
    # min_free_vms_amount = db.Column(db.Integer(), nullable=False, default=3)
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
    async def controller_obj(self):
        pool = await Pool.get(self.id)
        return await pool.controller_obj

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
                          template_id, datapool_id, increase_step,
                          initial_size, reserve_size, total_size, vm_name_template,
                          create_thin_clones, connection_types):
        """Nested transactions are atomic."""
        async with db.transaction() as tx:  # noqa
            # Create Pool
            await system_logger.debug(_('Create Pool {}').format(verbose_name))
            pool = await Pool.create(verbose_name=verbose_name,
                                     cluster_id=cluster_id,
                                     node_id=node_id,
                                     datapool_id=datapool_id,
                                     controller_ip=controller_ip,
                                     connection_types=connection_types)

            await system_logger.debug(_('Create AutomatedPool {}').format(verbose_name))
            # Create AutomatedPool
            automated_pool = await super().create(id=pool.id,
                                                  template_id=template_id,
                                                  min_size=POOL_MIN_SIZE,
                                                  max_size=POOL_MAX_SIZE,
                                                  max_vm_amount=POOL_MAX_VM_AMOUNT,
                                                  increase_step=increase_step,
                                                  max_amount_of_create_attempts=POOL_MAX_CREATE_ATTEMPTS,
                                                  initial_size=initial_size,
                                                  reserve_size=reserve_size,
                                                  total_size=total_size,
                                                  vm_name_template=vm_name_template,
                                                  create_thin_clones=create_thin_clones)

            await system_logger.info(_('AutomatedPool {} is created').format(verbose_name), entity=pool.entity)

            return automated_pool

    async def soft_update(self, creator, verbose_name, reserve_size, total_size, vm_name_template, keep_vms_on: bool,
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
                await system_logger.debug(_('Update Pool values for AutomatedPool {}').format(await self.verbose_name))
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
                desc = str(auto_pool_kwargs)
                await system_logger.info(_('Update AutomatedPool values for {}').format(await self.verbose_name),
                                         description=desc,
                                         user=creator,
                                         entity=self.entity
                                         )
                await self.update(**auto_pool_kwargs).apply()

        desc = str(pool_kwargs)
        automated_pool = await self.get(self.id)
        msg = _('Automated pool {name} updated.').format(name=await automated_pool.verbose_name)
        await system_logger.info(msg, description=desc, user=creator, entity=self.entity)

        return True

    async def add_vm(self):
        """Try to add VM to pool."""
        verbose_name = self.vm_name_template or await self.verbose_name  # temp???
        pool_controller = await self.controller_obj

        params = {
            'verbose_name': verbose_name,
            'domain_id': str(self.template_id),
            'datapool_id': str(await self.datapool_id),
            'controller_id': pool_controller.id,
            'node_id': str(await self.node_id),
            'create_thin_clones': self.create_thin_clones,
        }

        for i in range(self.max_amount_of_create_attempts):
            await system_logger.debug(_('add_domain {}, attempt № {}, of {}').format(
                verbose_name, i, self.max_amount_of_create_attempts))
            try:
                vm_info = await VmModel.copy(**params)
                current_vm_task_id = vm_info['task_id']
                await system_logger.debug('VM creation task id: {}'.format(current_vm_task_id))
            except VmCreationError:
                break

            def _check_if_vm_created(redis_message):
                try:
                    redis_message_data = redis_message['data'].decode()
                    redis_message_data_dict = json.loads(redis_message_data)
                    obj = redis_message_data_dict['object']
                    if current_vm_task_id == obj['parent'] and obj['status'] == 'SUCCESS':
                        return True
                except asyncio.CancelledError:
                    raise
                except Exception as ex:  # Нас интересует лишь прошла ли проверка
                    system_logger._debug('_check_if_vm_created ' + str(ex))

                return False

            try:
                is_vm_successfully_created = await a_redis_wait_for_message(
                    WS_MONITOR_CHANNEL_OUT, _check_if_vm_created, VEIL_WS_MAX_TIME_TO_WAIT)
                await system_logger.debug('Ws msg vm successfully_created: {}'.format(is_vm_successfully_created))

                # 2) determine if vm created by task status
                # if not is_vm_successfully_created:
                #    await system_logger.debug('Could`t get the response about result of creation VM on ECP by WS.')
                #    try:
                #        # TODO: сломалось при мердже - починить на новый клиент. Мб ваще выкинуть? Проверки по статусу
                #         вм достаточно
                #        # token = await controller_module.ControllerModel.get_token(controller_address)
                #        # veil_client = VeilHttpClient(controller_address, token=token)
                #        # is_vm_successfully_created = await veil_client.check_task_status(current_vm_task_id)
                #        raise NotImplementedError()
                #    except asyncio.CancelledError:
                #        raise
                #    except Exception as ex:  # Возможно множество исключений, но нас интнесует лишь их отсутствие
                #        await system_logger.error('Exception during task status checking: {}'.format(str(ex)))

                # 3) determine if vm created by vm status
                if not is_vm_successfully_created:
                    await system_logger.debug('Probably task is not done. Check VM status.')
                    domain_client = pool_controller.veil_client.domain(domain_id=vm_info['id'])
                    try:
                        await domain_client.info()
                        is_vm_successfully_created = domain_client.active
                    except asyncio.CancelledError:
                        raise
                    except Exception as ex:  # Возможно множество исключений, но нас интнесует лишь их отсутствие
                        await system_logger.error('Exception during vm status checking: {}'.format(str(ex)))

            except asyncio.CancelledError:
                # Если получили CancelledError в ходе ожидания создания вм,
                # то отменяем на контроллере таску создания вм. (CancelledError бросится например при мягком завршении
                # процесса воркера)
                try:
                    task_client = pool_controller.veil_client.task(task_id=current_vm_task_id)
                    await task_client.cancel()
                except Exception as ex:
                    await system_logger.error('Exception during vm creation task cancelling: {}'.format(str(ex)))
                raise

            # VM создается в любом случае, но если что-то пошло не так, то мы создаем ее в БД.
            vm_is_broken = False if is_vm_successfully_created else False
            await VmModel.create(id=vm_info['id'],
                                 pool_id=str(self.id),
                                 template_id=str(self.template_id),
                                 created_by_vdi=True,
                                 verbose_name=vm_info['verbose_name'],
                                 broken=vm_is_broken)

            pool = await Pool.get(self.id)
            await system_logger.info(
                _('VM {} is added to Automated pool {}').format(vm_info['verbose_name'], pool.verbose_name),
                entity=self.entity)

            return vm_info

        await self.deactivate()
        raise VmCreationError(_('Error with create VM {}').format(verbose_name))

    @property
    async def template_os_type(self):
        """Получает инфорацию об ОС шаблона от VeiL ECP."""
        pool_controller = await self.controller_obj
        veil_template = pool_controller.veil_client.domain(domain_id=str(self.template_id))
        await veil_template.info()
        return veil_template.os_type

    async def add_initial_vms(self):
        """Create required initial amount of VMs for auto pool
           Основная логика сохранена со старой схемы. На рефакторинг внутреннего кода нет времени.
           Главное, что бы хотелось тут и в других местах создания виртуалок - отправлять диапазоны виртуалок
        """

        # Fetching template info from controller.
        controller_address = await self.controller_ip
        verbose_name = await self.verbose_name

        await system_logger.debug('Add {} initial vms for pool {}. Controller.address: {}'.format(self.initial_size,
                                                                                                  verbose_name,
                                                                                                  controller_address))

        pool_os_type = await self.template_os_type

        await system_logger.debug(_('Pool {} os type is: {}').format(verbose_name, pool_os_type))
        await self.update(os_type=pool_os_type).apply()

        await system_logger.info(_('Automated pool creation started'), entity=self.entity)

        vm_list = list()
        # vm_index = 1

        try:
            for i in range(self.initial_size):
                vm = await self.add_vm()
                vm_list.append(vm)
                msg = _('Created {} VMs from {} at the Automated pool {}').format(i + 1, self.initial_size,
                                                                                  verbose_name)
                await system_logger.info(msg, entity=self.entity)

                # internal message about progress(WS)
                msg_dict = dict(msg=msg,
                                mgs_type='data',
                                event='pool_creation_progress',
                                pool_id=str(self.id),
                                domain_verbose_name=vm['verbose_name'],
                                initial_size=self.initial_size,
                                resource=VDI_TASKS_SUBSCRIPTION)

                REDIS_CLIENT.publish(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))

        except VmCreationError as vm_error:
            # log that we cant create required initial amount of VMs
            await system_logger.error(_('Can`t create VM'), entity=self.entity)
            await system_logger.debug(vm_error)

        # internal message about pool creation result (WS)
        is_creation_successful = (len(vm_list) == self.initial_size)
        await system_logger.debug('is_creation_successful {}'.format(is_creation_successful))
        if is_creation_successful:
            msg = _('Initial VM amount {} at the Automated pool {}').format(len(vm_list), verbose_name)
            await system_logger.info(msg, entity=self.entity)
        else:
            msg = _('Automated pool created with errors. VMs created: {}. Required: {}').format(len(vm_list),
                                                                                                self.initial_size)
            await system_logger.error(msg, entity=self.entity)

        msg_dict = dict(msg=msg,
                        msg_type='data',
                        event='pool_creation_completed',
                        pool_id=str(self.id),
                        amount_of_created_vms=len(vm_list),
                        initial_size=self.initial_size,
                        is_successful=is_creation_successful,
                        resource=VDI_TASKS_SUBSCRIPTION)

        REDIS_CLIENT.publish(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))

        # Пробросить исключение, если споткнулись на создании машин
        if not is_creation_successful:
            raise PoolCreationError(_('Could not create the required number of machines.'))

    async def remove_vms(self, creator):
        """Интерфейс для запуска команды HttpClient на удаление виртуалки"""

        await system_logger.debug(_('Delete VMs for AutomatedPool {}').format(await self.verbose_name))
        vms = await VmModel.query.where(VmModel.pool_id == self.id).gino.all()

        status = None
        for vm in vms:
            await system_logger.debug(_('Calling soft delete for vm {}').format(vm.verbose_name))
            status = await vm.soft_delete(creator=creator)
        return status
