# -*- coding: utf-8 -*-
import asyncio
from textwrap import wrap
import uuid
from enum import Enum
from sqlalchemy import and_, union_all, case, literal_column, desc, text, Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from asyncpg.exceptions import UniqueViolationError

from common.settings import POOL_MAX_CREATE_ATTEMPTS
from common.database import db

from common.veil.veil_gino import Status, EntityType, VeilModel
from common.veil.veil_graphene import VmState
from common.veil.veil_errors import VmCreationError, SimpleError, ValidationError, PoolCreationError
from common.utils import extract_ordering_data
from web_app.auth.license.utils import License
from common.veil.veil_redis import get_thin_clients_count

from common.models.auth import (User as UserModel, Entity as EntityModel, EntityOwner as EntityOwnerModel,
                                Group as GroupModel, UserGroup as UserGroupModel)
from common.models.authentication_directory import AuthenticationDirectory
from common.models.vm import Vm as VmModel
from common.models.task import Task

from common.languages import lang_init
from common.log.journal import system_logger

from web_app.front_ws_api.subscription_sources import POOLS_SUBSCRIPTION


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
        SPICE_DIRECT = 'SPICE_DIRECT'
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
                    users_count = db.func.count(text('anon_1.entity_owner_user_id'))
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
            AutomatedPool.increase_step,
            AutomatedPool.max_amount_of_create_attempts,
            AutomatedPool.initial_size,
            AutomatedPool.reserve_size,
            AutomatedPool.total_size,
            AutomatedPool.vm_name_template,
            AutomatedPool.os_type,
            AutomatedPool.create_thin_clones,
            AutomatedPool.prepare_vms,
            AutomatedPool.ad_cn_pattern,
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
                permissions_query = EntityModel.join(EntityOwnerModel.query.where(
                    (EntityOwnerModel.user_id == user_id) | (
                        EntityOwnerModel.group_id.in_(groups_ids_list))).alias())
            else:
                permission_outer = True
                permissions_query = EntityModel.join(EntityOwnerModel)

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
                AutomatedPool.increase_step,
                AutomatedPool.max_amount_of_create_attempts,
                AutomatedPool.initial_size,
                AutomatedPool.reserve_size,
                AutomatedPool.total_size,
                AutomatedPool.vm_name_template,
                AutomatedPool.os_type,
                AutomatedPool.create_thin_clones,
                AutomatedPool.prepare_vms,
                AutomatedPool.ad_cn_pattern,
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
        if not ordering:
            query = query.order_by(Pool.verbose_name)
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
        Надо бы переделать это в статический метод а то везде приходится делать Pool.get(id)
        """
        if only_free:
            ero_query = EntityOwnerModel.select('entity_id').where(EntityOwnerModel.user_id != None)  # noqa

            entity_query = EntityModel.select('entity_uuid').where(
                (EntityModel.entity_type == EntityType.VM) & (EntityModel.id.in_(ero_query)))

            vm_query = db.select([db.func.count()]).where(
                (VmModel.pool_id == self.id) & (VmModel.id.notin_(entity_query)) & (VmModel.status == Status.ACTIVE))  # noqa

            return await vm_query.gino.scalar()

        return await db.select([db.func.count()]).where(VmModel.pool_id == self.id).gino.scalar()

    def get_user_vms_query(self, user_id):
        """Формирует запрос всех ВМ пользователя с учетом его прав.

        Сочитание pool id и username уникальное, т.к. пользователь не может иметь больше одной машины в пуле.
        """
        # TODO: очень странный блок. По идее self.assigned_users не нужен - протестировать
        # Deprecated 21.10.2020
        # assigned_users = await self.assigned_users
        # if user_id not in [user[0] for user in assigned_users]:
        #     return
        # Список всех ВМ пользователя
        entity_query = EntityModel.select('entity_uuid').where(
            (EntityModel.entity_type == EntityType.VM) & (
                EntityModel.id.in_(
                    EntityOwnerModel.select('entity_id').where(EntityOwnerModel.user_id == user_id))))
        vm_query = VmModel.query.where((VmModel.id.in_(entity_query)) & (VmModel.pool_id == self.id))
        return vm_query

    async def get_vm(self, user_id):
        """Возвращает ВМ пользователя с учетом его прав.

        Сочитание pool id и username уникальное, т.к. пользователь не может иметь больше одной машины в пуле.
        """
        await system_logger.debug('Возвращаем ВМ пользователя')
        return await self.get_user_vms_query(user_id).gino.first()

    # @property
    # async def roles(self):
    #     """Уникальные роли назначенные пулу (без учета групп и пользователей)."""
    #     query = EntityModel.query.where(
    #         (EntityModel.entity_type == EntityType.POOL) & (EntityModel.entity_uuid == self.id)).alias()
    #     filtered_query = EntityOwnerModel.join(query).select().alias()
    #     result_query = db.select([text('anon_1.role')]).select_from(filtered_query).group_by('role')
    #     return await result_query.gino.all()

    @property
    def assigned_groups_query(self):
        """Группы назначенные пулу."""
        query = EntityModel.query.where((EntityModel.entity_type == EntityType.POOL) & (EntityModel.entity_uuid == self.id)).alias()
        return GroupModel.join(EntityOwnerModel.join(query).alias()).select()

    @property
    async def assigned_groups(self):
        return await self.assigned_groups_query.gino.load(GroupModel).all()

    async def assigned_groups_paginator(self, limit, offset):
        return await self.assigned_groups_query.limit(limit).offset(offset).gino.load(GroupModel).all()

    @property
    async def possible_groups(self):
        query = EntityModel.query.where((EntityModel.entity_type == EntityType.POOL) & (EntityModel.entity_uuid == self.id)).alias()
        filtered_query = GroupModel.join(EntityOwnerModel.join(query).alias(), isouter=True).select().where(text('anon_1.entity_owner_group_id is null'))  # noqa
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
        users_query = EntityOwnerModel.join(query)
        user_query_ids = db.select([text('user_id')]).select_from(users_query)

        # Список пользователей состоящих в группах
        group_users_query = UserGroupModel.join(GroupModel).join(EntityOwnerModel.join(query))
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
        group_users_query = UserGroupModel.join(GroupModel).join(EntityOwnerModel.join(query).alias()).select().alias()
        group_users_ids = db.select([text('anon_7.user_id')]).select_from(group_users_query).alias()

        # Список явных пользователей
        users_query = EntityOwnerModel.join(query).select().alias()
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
                ero = await EntityOwnerModel.create(entity_id=entity.id, user_id=user_id)
                user = await UserModel.get(user_id)
                await system_logger.info(
                    _('User {} has been included to pool {}.').format(user.username, self.verbose_name),
                    user=creator,
                    entity=self.entity)
        except UniqueViolationError:
            raise SimpleError(_('{} already has permission.').format(type(self).__name__), user=creator,
                              entity=self.entity)
        return ero

    async def remove_users(self, creator: str, users_list: list):
        # updated 17.12.2020
        entity = EntityModel.select('id').where(
            (EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id))

        for user_id in users_list:
            has_permission = await EntityOwnerModel.query.where(
                (EntityOwnerModel.user_id == user_id) & (EntityOwnerModel.entity_id == entity)).gino.first()
            user = await UserModel.get(user_id)
            if has_permission:
                await system_logger.info(_('Removing user {} from pool {}.').format(user.username, self.verbose_name),
                                         user=creator,
                                         entity=self.entity)
            else:
                await system_logger.warning(
                    _('User {} has no direct right to pool {}.').format(user.username, self.verbose_name),
                    user=creator,
                    entity=self.entity)

        # entity = EntityModel.select('id').where((EntityModel.entity_type == self.entity_type)
        # & (EntityModel.entity_uuid == self.id))

        operation_status = await EntityOwnerModel.delete.where(
            (EntityOwnerModel.user_id.in_(users_list)) & (EntityOwnerModel.entity_id == entity)).gino.status()
        return operation_status

    async def add_group(self, group_id, creator):
        entity = await self.entity_obj

        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityOwnerModel.create(entity_id=entity.id, group_id=group_id)
                group = await GroupModel.get(group_id)
                await system_logger.info(
                    _('Group {} has been included to pool {}.').format(group.verbose_name, self.verbose_name),
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
            await system_logger.info(_('Removing group {} from pool {}.').format(group.verbose_name, self.verbose_name),
                                     user=creator,
                                     entity=self.entity
                                     )
        entity = EntityModel.select('id').where((EntityModel.entity_type == self.entity_type) & (EntityModel.entity_uuid == self.id))
        return await EntityOwnerModel.delete.where(
            (EntityOwnerModel.group_id.in_(groups_list)) & (EntityOwnerModel.entity_id == entity)).gino.status()

    async def free_assigned_vms(self, users_list: list):
        """
        Будут удалены все записи из EntityOwner соответствующие условию.
        Запрос такой ублюдский, потому что через Join в текущей версии Gino получалось очень много подзапросов.
        :param users_list: uuid пользователей для которых выполняется поиск
        :return: gino.status()
        """
        # from common.models import VmModel
        entity_query = EntityModel.select('id').where((EntityModel.entity_type == EntityType.VM) & (
            EntityModel.entity_uuid.in_(VmModel.select('id').where(VmModel.pool_id == self.id))))

        ero_query = EntityOwnerModel.delete.where(
            EntityOwnerModel.entity_id.in_(entity_query) & EntityOwnerModel.user_id.in_(users_list))

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

        # Оповещаем о создании пула
        await pool.publish_data_in_internal_channel('CREATED')

        return pool

    async def full_delete(self, creator):
        """Удаление сущности с удалением зависимых сущностей"""

        old_status = self.status  # Запомнить теущий статус
        try:
            await self.set_status(Status.DELETING)

            automated_pool = await AutomatedPool.get(self.id)

            if automated_pool:
                await system_logger.debug(_('Delete VMs for AutomatedPool {}.').format(self.verbose_name))
                vm_ids = await VmModel.get_vms_ids_in_pool(self.id)
                await VmModel.remove_vms(vm_ids, creator, True)

            await self.delete()
            msg = _('Complete removal pool of desktops {verbose_name} is done.').format(verbose_name=self.verbose_name)
            await system_logger.info(msg, entity=self.entity, user=creator)

        except Exception:
            # Если возникло исключение во время удаления то возвращаем пред. статус
            await self.set_status(old_status)
            raise

        # Оповещаем об удалении пула
        await self.publish_data_in_internal_channel('DELETED')
        return True

    @staticmethod
    async def delete_pool(pool, creator):
        return await pool.full_delete(creator)

    @classmethod
    async def activate(cls, pool_id):
        pool = await Pool.get(pool_id)
        await pool.set_status(Status.ACTIVE)
        entity = {'entity_type': EntityType.POOL, 'entity_uuid': pool_id}
        # Активация ВМ. Добавлено 02.11.2020 - не факт, что нужно.
        vms = await VmModel.query.where(VmModel.pool_id == pool_id).gino.all()
        for vm in vms:
            await vm.update(status=Status.ACTIVE).apply()
        await system_logger.info(_('Pool {} has been activated.').format(pool.verbose_name), entity=entity)
        return True

    @classmethod
    async def deactivate(cls, pool_id):
        pool = await Pool.get(pool_id)
        await pool.set_status(Status.FAILED)
        entity = {'entity_type': EntityType.POOL, 'entity_uuid': pool_id}
        # Деактивация ВМ. Добавлено 02.11.2020 - не факт, что нужно.
        vms = await VmModel.query.where(VmModel.pool_id == pool_id).gino.all()
        for vm in vms:
            await vm.update(status=Status.FAILED).apply()
        await system_logger.warning(_('Pool {} has been deactivated.').format(pool.verbose_name), entity=entity)
        return True

    @classmethod
    async def enable(cls, pool_id):
        """Отличается от activate тем, что проверяет предыдущий статус."""
        pool = await Pool.get(pool_id)
        # Т.к. сейчас нет возможности остановить создание пула - не трогаем не активные
        if pool.status == Status.FAILED:
            return await pool.activate(pool.id)
        return False

    async def get_free_vm_v2(self):
        """Возвращает случайную свободную ВМ.
        Свободная == не занятая за кем-то конкретном.
        Приоритетной будет та, что включена."""
        # Формируем список ВМ
        entity_query = EntityModel.select('entity_uuid').where(
            (EntityModel.entity_type == EntityType.VM) & (EntityModel.id.in_(EntityOwnerModel.select('entity_id'))))
        vm_query = VmModel.select('id').where(
            (VmModel.pool_id == self.id) & (VmModel.status == Status.ACTIVE) & (VmModel.id.notin_(entity_query)))

        vm_ids_data = await vm_query.gino.all()
        if not vm_ids_data:
            return
        # Получаем набор уникальных ids ВМ
        vm_ids = set(str(vm_id) for (vm_id,) in vm_ids_data)
        # Исключительно для удобства дебага
        vm_id = None
        # Запрашиваем на ECP VeiL включенные ВМ из списка
        ids_str = ','.join(vm_ids)
        pool_controller = await self.controller_obj
        # Полученный список может оказаться больше, чем кол-во параметров принимаемых VeiL, поэтому делим его на блоки
        # Т.к. список формируется выше, мы предполагаем, что 157 id и запятая уложится в 5809 символов
        max_ids_length = 5809
        ids_str_list = wrap(ids_str, width=max_ids_length)
        # теперь получаем данные для каждого блока id
        for ids_str_section in ids_str_list:
            controller_client = pool_controller.veil_client
            if not controller_client:
                break
            domains_list_response = await controller_client.domain().list(fields=['id'],
                                                                          params={'user_power_state': 'ON',
                                                                                  'ids': ids_str_section})
            if domains_list_response.success and domains_list_response.paginator_results:
                # Берем первый идентиифкатор
                vm_id = domains_list_response.paginator_results[0].get('id')
                break
        if not vm_id:
            vm_id = vm_ids_data[0][0]

        return await VmModel.get(vm_id)

    async def get_vms_info(self):
        """Возвращает информацию для всех ВМ в пуле."""
        from web_app.pool.schema import VmType
        # Получаем список ВМ
        vms = await self.vms

        if not vms:
            return
        # Получаем набор уникальных ids ВМ
        vm_ids = set(str(vm.id) for vm in vms)
        ids_str = ','.join(vm_ids)
        pool_controller = await self.controller_obj

        # Полученный список может оказаться больше, чем кол-во параметров принимаемых VeiL, поэтому делим его на блоки
        # Т.к. список формируется выше, мы предполагаем, что 157 id и запятая уложится в 5809 символов
        max_ids_length = 5809
        ids_str_list = wrap(ids_str, width=max_ids_length)

        # Получаем данные для каждого блока id
        vms_list = list()
        for ids_str_section in ids_str_list:
            # Запрашиваем на ECP VeiL данные
            fields = ['id', 'user_power_state', 'parent', 'status', 'guest_utils']
            controller_client = pool_controller.veil_client
            if not controller_client:
                break
            domains_list_response = await controller_client.domain().list(fields=fields,
                                                                          params={'ids': ids_str_section})
            vms_list += domains_list_response.paginator_results

        vms_dict = dict()
        for vm_info in vms_list:
            vm_info['parent_name'] = None
            # Получаем имя шаблона
            if vm_info['parent']:
                vm_info['parent_name'] = vm_info['parent']['verbose_name']
            del vm_info['parent']
            vms_dict[vm_info['id']] = vm_info

        vms_info = list()
        guest_utils = None
        qemu_state = None
        for vm in vms:
            # TODO: Добавить принадлежность к домену + на фронте
            user_power_state = VmState.UNDEFINED
            vm_status = Status.FAILED  # Если с вейла не пришла инфа, то вм считается в статусе FAILED
            parent_name = None
            for vm_id in vms_dict.keys():
                if str(vm_id) == str(vm.id):
                    user_power_state = vms_dict[vm_id]['user_power_state']
                    parent_name = vms_dict[vm_id]['parent_name']
                    vm_status = Status(vms_dict[vm_id]['status'])
                    guest_utils = vms_dict[vm_id].get('guest_utils')
                    qemu_state = guest_utils.get('qemu_state', False) if guest_utils else False

            # update status
            if vm.status != Status.SERVICE:
                await vm.update(status=vm_status).apply()

            # Формируем список с информацией по каждой вм в пуле
            vms_info.append(
                VmType(user_power_state=user_power_state,
                       parent_name=parent_name,
                       qemu_state=3 if qemu_state else 1,
                       **vm.__values__))
        return vms_info

    async def free_user_vms(self, user_id):
        """Т.к. на тонком клиенте нет выбора VM - будут сложности если у пользователя несколько VM в рамках 1 пула."""
        # from common.models import VmModel
        vms_query = VmModel.select('id').where(VmModel.pool_id == self.id)
        entity_query = EntityModel.select('id').where(
            (EntityModel.entity_type == EntityType.VM) & (EntityModel.entity_uuid.in_(vms_query)))
        exists_count = await db.select([db.func.count()]).where((EntityOwnerModel.user_id == user_id) & (
            EntityOwnerModel.entity_id.in_(entity_query))).gino.scalar()
        if exists_count > 0:
            role_owner_query = EntityOwnerModel.select('entity_id').where(
                (EntityOwnerModel.user_id == user_id) & (EntityOwnerModel.entity_id.in_(entity_query)))
            exists_vm_query = EntityModel.select('entity_uuid').where(EntityModel.id.in_(role_owner_query))
            await VmModel.update.values(status=Status.SERVICE).where(VmModel.id.in_(exists_vm_query)).gino.status()
        ero_query = EntityOwnerModel.delete.where(
            (EntityOwnerModel.user_id == user_id) & (EntityOwnerModel.entity_id.in_(entity_query)))

        return await ero_query.gino.status()

    # override
    def get_resource_type(self):
        return POOLS_SUBSCRIPTION

    # override
    async def additional_model_to_json_data(self):
        pool_type = await self.pool_type
        return dict(pool_type=pool_type)


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
    def vms_on_same_node(node_id: str, veil_vm_data: list) -> bool:
        """Проверка, что все VM находятся на одной Veil node.

        All VMs are on the same node and cluster, all VMs have the same datapool
        so we can take this data from the first item
        """
        return all(vm_data['node']['id'] == node_id for vm_data in veil_vm_data)

    @classmethod
    async def soft_create(cls, creator, veil_vm_data: list, verbose_name: str,
                          controller_address: str, cluster_id: str, node_id: str,
                          datapool_id: str, connection_types: list):
        """Nested transactions are atomic."""
        async with db.transaction() as tx:  # noqa
            await system_logger.debug(_('StaticPool: Create Pool.'))
            pl = await Pool.create(verbose_name=verbose_name,
                                   controller_ip=controller_address,
                                   cluster_id=cluster_id,
                                   node_id=node_id,
                                   datapool_id=datapool_id,
                                   connection_types=connection_types)

            await system_logger.debug(_('StaticPool: Create StaticPool.'))
            pool = await super().create(id=pl.id)
            await system_logger.debug(_('StaticPool: Create VMs.'))
            # TODO: эксперементальное обновление
            for vm_type in veil_vm_data:
                await VmModel.create(id=vm_type.id,
                                     verbose_name=vm_type.verbose_name,
                                     pool_id=pool.id,
                                     template_id=None,
                                     created_by_vdi=False)
                await system_logger.debug(_('VM {} created.').format(vm_type.verbose_name))

            await system_logger.info(_('Static pool {} created.').format(verbose_name), user=creator,
                                     entity=pool.entity)
            await pool.activate()
        return pool

    @classmethod
    async def soft_update(cls, id, verbose_name, keep_vms_on, connection_types, creator):
        old_pool_obj = await Pool.get(id)
        async with db.transaction() as tx:  # noqa
            update_type, update_dict = await Pool.soft_update(id, verbose_name=verbose_name,
                                                              keep_vms_on=keep_vms_on,
                                                              connection_types=connection_types,
                                                              creator=creator
                                                              )

            msg = _('Pool {} has been updated.').format(old_pool_obj.verbose_name)
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
    increase_step = db.Column(db.Integer(), nullable=False, default=3)
    # min_free_vms_amount = db.Column(db.Integer(), nullable=False, default=3)
    max_amount_of_create_attempts = db.Column(db.Integer(), nullable=False, default=2)
    initial_size = db.Column(db.Integer(), nullable=False, default=1)
    reserve_size = db.Column(db.Integer(), nullable=False, default=0)
    total_size = db.Column(db.Integer(), nullable=False, default=1)  # Размер пула
    vm_name_template = db.Column(db.Unicode(length=100), nullable=True)
    os_type = db.Column(db.Unicode(length=100), nullable=True)
    create_thin_clones = db.Column(db.Boolean(), nullable=False, default=True)
    prepare_vms = db.Column(db.Boolean(), nullable=False, default=True)
    # Группы/Контейнеры в Active Directory для назначения виртуальным машинам пула
    ad_cn_pattern = db.Column(db.Unicode(length=1000), nullable=True)

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
    async def soft_create(cls, creator, verbose_name, controller_ip, cluster_id, node_id,
                          template_id, datapool_id, increase_step,
                          initial_size, reserve_size, total_size, vm_name_template,
                          create_thin_clones, prepare_vms, connection_types, ad_cn_pattern: str = None):
        """Nested transactions are atomic."""
        async with db.transaction() as tx:  # noqa
            # Создаем базовую сущность Pool
            pool = await Pool.create(verbose_name=verbose_name,
                                     cluster_id=cluster_id,
                                     node_id=node_id,
                                     datapool_id=datapool_id,
                                     controller_ip=controller_ip,
                                     connection_types=connection_types)
            # Создаем AutomatedPool
            automated_pool = await super().create(id=pool.id,
                                                  template_id=template_id,
                                                  increase_step=increase_step,
                                                  max_amount_of_create_attempts=POOL_MAX_CREATE_ATTEMPTS,
                                                  initial_size=initial_size,
                                                  reserve_size=reserve_size,
                                                  total_size=total_size,
                                                  vm_name_template=vm_name_template,
                                                  create_thin_clones=create_thin_clones,
                                                  prepare_vms=prepare_vms,
                                                  ad_cn_pattern=ad_cn_pattern)
            # Записываем событие в журнал
            description = _('Initial_size: {}, total_size: {}, increase_step {}, reserve_size {}.').format(
                initial_size, total_size, increase_step, reserve_size)
            await system_logger.info(_('AutomatedPool {} is created.').format(verbose_name), user=creator,
                                     entity=pool.entity, description=description)
            return automated_pool

    async def soft_update(self, creator, verbose_name, reserve_size, total_size, increase_step, vm_name_template,
                          keep_vms_on: bool, create_thin_clones: bool, prepare_vms: bool, connection_types, ad_cn_pattern):
        pool_kwargs = dict()
        auto_pool_kwargs = dict()
        old_verbose_name = await self.verbose_name
        async with db.transaction() as tx:  # noqa
            # Update Pool values
            if verbose_name:
                pool_kwargs['verbose_name'] = verbose_name
            if isinstance(keep_vms_on, bool):
                pool_kwargs['keep_vms_on'] = keep_vms_on
            if connection_types:
                pool_kwargs['connection_types'] = connection_types

            if pool_kwargs:
                await system_logger.debug(_('Update Pool values for AutomatedPool {}.').format(await self.verbose_name))
                pool = await Pool.get(self.id)
                await pool.update(**pool_kwargs).apply()

            # Update AutomatedPool values
            if reserve_size:
                auto_pool_kwargs['reserve_size'] = reserve_size
            if total_size:
                auto_pool_kwargs['total_size'] = total_size
            if increase_step:
                auto_pool_kwargs['increase_step'] = increase_step
            if vm_name_template:
                auto_pool_kwargs['vm_name_template'] = vm_name_template
            if ad_cn_pattern:
                auto_pool_kwargs['ad_cn_pattern'] = ad_cn_pattern
            if isinstance(create_thin_clones, bool):
                auto_pool_kwargs['create_thin_clones'] = create_thin_clones
            if isinstance(prepare_vms, bool):
                auto_pool_kwargs['prepare_vms'] = prepare_vms
            if auto_pool_kwargs:
                desc = str(auto_pool_kwargs)
                await system_logger.debug(_('Update AutomatedPool values for {}.').format(await self.verbose_name),
                                          description=desc,
                                          user=creator,
                                          entity=self.entity)
                await self.update(**auto_pool_kwargs).apply()
        # Событие о редакировании пула
        pool_kwargs.update(auto_pool_kwargs)
        msg = _('Pool {} has been updated.').format(old_verbose_name)
        await system_logger.info(message=msg, description=str(pool_kwargs), user=creator, entity=self.entity)
        return True

    async def add_vm(self):
        """Try to add VM to pool."""
        verbose_name = self.vm_name_template or await self.verbose_name  # temp???
        pool_controller = await self.controller_obj
        # Прерываем выполнение при отсутствии клиента
        if not pool_controller.veil_client:
            raise AssertionError(_('There is no client for pool {}.').format(self.verbose_name))

        # Перебор имени ВМ на контроллере учитывает индекс в имени. Если ВМ-1 будет занята, то произойдет инкремент
        params = {
            'verbose_name': verbose_name + '-1',
            'domain_id': str(self.template_id),
            'datapool_id': str(await self.datapool_id),
            'controller_id': pool_controller.id,
            'node_id': str(await self.node_id),
            'create_thin_clones': self.create_thin_clones,
        }

        for i in range(self.max_amount_of_create_attempts):  # noqa
            try:
                vm_info = await VmModel.copy(**params)
                current_vm_task_id = vm_info['task_id']
                await system_logger.debug('VM creation task id: {}'.format(current_vm_task_id))
            except VmCreationError:
                break

            # Ожидаем завершения создания ВМ
            try:
                task_completed = False
                task_client = pool_controller.veil_client.task(task_id=current_vm_task_id)
                while not task_completed:
                    await asyncio.sleep(5)
                    task_completed = await task_client.finished
                # Если задача выполнена с ошибкой - прерываем выполнение
                task_success = await task_client.success
                if not task_success:
                    raise VmCreationError(
                        _('VM creation task {} finished with error.').format(task_client.api_object_id))
            except asyncio.CancelledError:
                # Если получили CancelledError в ходе ожидания создания вм,
                # то отменяем на контроллере таску создания вм. (CancelledError бросится например при мягком завршении
                # процесса воркера)
                try:
                    task_client = pool_controller.veil_client.task(task_id=current_vm_task_id)
                    await task_client.cancel()
                except Exception as ex:
                    msg = _('Fail to cancel VM creation task.')
                    entity = {'entity_type': EntityType.VM, 'entity_uuid': None}
                    await system_logger.debug(message=msg, description=str(ex), entity=entity)
                raise

            # Получаем актуальное имя виртуальной машины присвоенное контроллером
            veil_domain = pool_controller.veil_client.domain(vm_info['id'])
            await veil_domain.info()
            # создаем запись в БД
            vm_object = await VmModel.create(id=vm_info['id'],
                                             pool_id=str(self.id),
                                             template_id=str(self.template_id),
                                             created_by_vdi=True,
                                             verbose_name=veil_domain.verbose_name)

            pool = await Pool.get(self.id)
            msg = _('VM {} created.').format(veil_domain.verbose_name)
            description = _('VM {} created and added to the pool {}.').format(veil_domain.verbose_name,
                                                                              pool.verbose_name)
            await system_logger.info(message=msg, description=description,
                                     entity=self.entity)
            # Раньше возвращали vm_info, но для упрощения вызова подготовки ВМ заменили на объект модели
            return vm_object

        await self.deactivate()
        raise VmCreationError(_('Attempts to create VM {} have been exhausted.').format(verbose_name))

    @property
    async def template_os_type(self):
        """Получает инфорацию об ОС шаблона от VeiL ECP."""
        pool_controller = await self.controller_obj
        if not pool_controller.veil_client:
            return
        veil_template = pool_controller.veil_client.domain(domain_id=str(self.template_id))
        await veil_template.info()
        return veil_template.os_type

    async def add_initial_vms(self):
        """Create required initial amount of VMs for auto pool."""
        # Fetching template info from controller.
        verbose_name = await self.verbose_name
        pool_os_type = await self.template_os_type
        await self.update(os_type=pool_os_type).apply()

        pool = await Pool.get(self.id)
        # В пуле уже могут быть машины, например, если инициализация пула была прервана из-за завершения приложения.
        num_of_vms_in_pool = await pool.get_vm_amount()
        try:
            for _i in range(num_of_vms_in_pool, self.initial_size):
                await self.add_vm()
                num_of_vms_in_pool += 1
                # update progress of associated task
                progress = (num_of_vms_in_pool / self.initial_size) * 100  # from 0 to 100
                await Task.set_progress_to_task_associated_with_entity(self.id, progress)
        except VmCreationError as vm_error:
            # log that we can`t create required initial amount of VMs
            await system_logger.error(_('VM creation error.'), entity=self.entity, description=str(vm_error))

        creation_successful = (self.initial_size <= num_of_vms_in_pool)
        if creation_successful:
            msg = _('{} vm(s) are successfully added in the {} pool.').format(self.initial_size, verbose_name)
            await system_logger.info(msg, entity=self.entity)
        else:
            msg = _('Adding VM to the pool {} finished with errors.').format(verbose_name)
            description = _('Required: {}, created: {}.').format(self.initial_size, num_of_vms_in_pool)
            await system_logger.error(message=msg, entity=self.entity, description=description)
            #  исключение не лишнее, без него таска завершится с FINISHED а не FAILED Перехватится в InitPoolTask
            raise PoolCreationError(msg)  # Пробросить исключение, если споткнулись на создании машин

    async def prepare_initial_vms(self):
        """Подготавливает ВМ для дальнейшего использования тонким клиентом."""
        vm_objects = await VmModel.query.where(VmModel.pool_id == self.id).gino.all()
        if not vm_objects:
            return
        active_directory_object = await AuthenticationDirectory.query.where(
            AuthenticationDirectory.status == Status.ACTIVE).gino.first()
        await asyncio.gather(
            *[vm_object.prepare_with_timeout(active_directory_object, self.ad_cn_pattern) for vm_object in vm_objects],
            return_exceptions=True)

    async def check_if_total_size_reached(self):

        pool = await Pool.get(self.id)
        vm_amount = await pool.get_vm_amount()
        return vm_amount >= self.total_size

    async def check_if_not_enough_free_vms(self):

        pool = await Pool.get(self.id)
        free_vm_amount = await pool.get_vm_amount(only_free=True)
        return free_vm_amount < self.reserve_size
