# -*- coding: utf-8 -*-
import asyncio
import json
import random
import uuid
from enum import Enum
from json.decoder import JSONDecodeError
from textwrap import wrap

from asyncpg.exceptions import UniqueViolationError

from sqlalchemy import (
    Enum as AlchemyEnum,
    UniqueConstraint,
    and_,
    case,
    desc,
    literal_column,
    text,
    union_all,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func

from veil_api_client import (
    TagConfiguration,
    VeilApiObjectStatus,
    VeilEntityConfiguration,
    VeilRestPaginator,
    VeilRetryConfiguration,
)

from common.database import db
from common.languages import _local_
from common.log.journal import system_logger
from common.models.auth import (
    Entity as EntityModel,
    EntityOwner as EntityOwnerModel,
    Group as GroupModel,
    User as UserModel,
    UserGroup as UserGroupModel,
)
from common.models.authentication_directory import AuthenticationDirectory
from common.models.task import Task
from common.models.vm import Vm as VmModel, VmActionUponUserDisconnect
from common.settings import (
    DEFAULT_NAME,
    DOMAIN_CREATION_MAX_STEP,
    POOL_MAX_CREATE_ATTEMPTS,
    VEIL_DEFAULT_VM_DISCONNECT_ACTION_TIMEOUT,
    VEIL_GUEST_AGENT_WIN_PATH,
    VEIL_MAX_IDS_LEN,
    VEIL_OPERATION_WAITING
)
from common.subscription_sources import POOLS_SUBSCRIPTION, WsEventToClient
from common.utils import extract_ordering_data
from common.veil.veil_errors import (
    PoolCreationError,
    SimpleError,
    ValidationError,
    VmCreationError
)
from common.veil.veil_gino import AbstractSortableStatusModel, EntityType, Status, VeilModel
from common.veil.veil_graphene import VmState
from common.veil.veil_redis import publish_data_in_internal_channel


class Pool(VeilModel):
    """Сейчас отсутствует смысловая валидация на уровне таблиц (она в схемах)."""

    class PoolTypes(Enum):
        """Доступные типы пулов."""

        AUTOMATED = "AUTOMATED"
        STATIC = "STATIC"
        GUEST = "GUEST"
        RDS = "RDS"

    class PoolConnectionTypes(Enum):
        """Типы подключений к ВМ, доступные пулу."""

        SPICE = "SPICE"
        SPICE_DIRECT = "SPICE_DIRECT"
        RDP = "RDP"
        NATIVE_RDP = "NATIVE_RDP"
        LOUDPLAY = "LOUDPLAY"

        @classmethod
        def values(cls):
            return [conn_type.value for conn_type in cls]

    __tablename__ = "pool"

    EXTRA_ORDER_FIELDS = ["controller_address", "users_count", "vm_amount"]

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4, unique=True)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    resource_pool_id = db.Column(UUID(), nullable=True)
    datapool_id = db.Column(UUID(), nullable=True)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)
    controller = db.Column(
        UUID(), db.ForeignKey("controller.id", ondelete="CASCADE"), nullable=False
    )
    keep_vms_on = db.Column(db.Boolean(), nullable=False, default=False)
    free_vm_from_user = db.Column(db.Boolean(), nullable=False, default=False)
    connection_types = db.Column(
        ARRAY(AlchemyEnum(PoolConnectionTypes)), nullable=False, index=True
    )
    tag = db.Column(UUID(), nullable=True)

    pool_type = db.Column(AlchemyEnum(PoolTypes), nullable=False)

    vm_action_upon_user_disconnect = db.Column(AlchemyEnum(VmActionUponUserDisconnect), nullable=False,
                                               default=VmActionUponUserDisconnect.NONE)
    vm_disconnect_action_timeout = db.Column(db.Integer(), nullable=False,
                                             default=VEIL_DEFAULT_VM_DISCONNECT_ACTION_TIMEOUT)  # на дисконнект юзера

    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated = db.Column(db.DateTime(timezone=True), server_default=func.now())
    creator = db.Column(db.Unicode(length=128), default="system")

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    def id_str(self):
        return str(self.id)

    @property
    async def possible_connection_types(self):
        return [
            connection_type
            for connection_type in self.PoolConnectionTypes
            if connection_type not in self.connection_types
        ]

    @property
    def entity_type(self):
        return EntityType.POOL

    @property
    async def controller_obj(self):
        from common.models.controller import Controller

        return await Controller.get(self.controller)

    async def get_vms(self, limit=None, offset=0, verbose_name=None):
        """Возвращаем виртуальные машины привязанные к пулу.

        Если limit is None, то возвращаем все машины (игнорируя offset)
        """
        query = VmModel.query.where(VmModel.pool_id == self.id).order_by(
            VmModel.verbose_name)

        if verbose_name:
            query = query.where(VmModel.verbose_name.ilike("%{}%".format(verbose_name))).order_by(
                VmModel.verbose_name)

        if limit is None:
            return await query.gino.all()
        else:
            return await query.limit(limit).offset(offset).gino.all()

    @property
    async def template_id(self):
        """Возвращает template_id для автоматического или гостевого пула, либо null."""
        template_id = (
            await AutomatedPool.select("template_id")
            .where(AutomatedPool.id == self.id)
            .gino.scalar()
        )
        return template_id

    @staticmethod
    def pool_tag_colour():
        return "#%02X%02X%02X" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )

    @staticmethod
    def build_ordering(query, ordering=None):
        """Построение порядка сортировки."""
        from common.models.controller import Controller

        if not ordering or not isinstance(ordering, str):
            return query

        # Определяем порядок сортировки по наличию "-" вначале строки
        (ordering, reversed_order) = extract_ordering_data(ordering)

        try:
            if ordering in Pool.EXTRA_ORDER_FIELDS:
                if ordering == "controller_address":
                    query = (
                        query.order_by(desc(Controller.address))
                        if reversed_order
                        else query.order_by(Controller.address)
                    )
                elif ordering == "users_count":
                    users_count = db.func.count(text("anon_1.entity_owner_user_id"))
                    query = (
                        query.order_by(desc(users_count))
                        if reversed_order
                        else query.order_by(users_count)
                    )
                elif ordering == "vm_amount":
                    vms_count = db.func.count(VmModel.id)
                    query = (
                        query.order_by(desc(vms_count))
                        if reversed_order
                        else query.order_by(vms_count)
                    )
            else:
                # Соответствие переданного наименования поля полю модели, чтобы не использовать raw_sql в order
                query = (
                    query.order_by(desc(getattr(Pool, ordering)))
                    if reversed_order
                    else query.order_by(getattr(Pool, ordering))
                )
        except AttributeError:
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(
                _local_("Incorrect sorting option {}.").format(ordering), entity=entity
            )
        return query

    @staticmethod
    def get_pools_query(
        ordering="verbose_name", user_id=None, groups_ids_list=None, role_set=None,
        get_favorite_only=False, is_superuser=False
    ):
        from common.models.controller import Controller

        # Формирование общего селекта из таблиц пулов
        select_fields = [
            Pool.id.label("master_id"),
            Pool.verbose_name,
            Pool.resource_pool_id,
            Pool.datapool_id,
            Pool.status,
            Pool.controller,
            Pool.keep_vms_on,
            Pool.free_vm_from_user,
            Pool.vm_action_upon_user_disconnect,
            Pool.vm_disconnect_action_timeout,
            AutomatedPool.template_id,
            AutomatedPool.increase_step,
            AutomatedPool.max_amount_of_create_attempts,
            AutomatedPool.initial_size,
            AutomatedPool.reserve_size,
            AutomatedPool.total_size,
            AutomatedPool.vm_name_template,
            AutomatedPool.os_type,
            AutomatedPool.create_thin_clones,
            AutomatedPool.enable_vms_remote_access,
            AutomatedPool.start_vms,
            AutomatedPool.set_vms_hostnames,
            AutomatedPool.include_vms_in_ad,
            AutomatedPool.ad_ou,
            Pool.pool_type,
            Pool.connection_types,
            Pool.created,
            Pool.updated,
            Pool.creator
        ]

        if user_id:
            # Признак добавлен ли пул в избранные
            select_fields.append(db.func.count(case(
                [((UserFavoritePool.user_id == user_id), UserFavoritePool.id)],
                else_=literal_column("NULL"))
            ).label("favorite"))

        query = db.select(select_fields)

        if ordering or user_id:
            # Добавляем пересечение с дополнительными внешними таблицами для возможности сортировки
            # permissions to use pools
            # super user имеет разрешение на все пулы, поэтому для него нет проверок на разрешения
            if not is_superuser and (user_id or groups_ids_list):
                if not groups_ids_list or not isinstance(groups_ids_list, list):
                    groups_ids_list = list()
                permission_outer = False
                permissions_query = EntityModel.join(
                    EntityOwnerModel.query.where(
                        (EntityOwnerModel.user_id == user_id)
                        | (EntityOwnerModel.group_id.in_(groups_ids_list))  # noqa: W503
                    ).alias()
                )
            else:
                permission_outer = True
                permissions_query = EntityModel.join(EntityOwnerModel)

            query = query.select_from(
                Pool.join(AutomatedPool, isouter=True)
                    .join(RdsPool, isouter=True)
                    .join(Controller, isouter=True)
                    .join(VmModel, isouter=True)
                    .join(
                    permissions_query.alias(),
                    (Pool.id == text("entity_entity_uuid")),
                    isouter=permission_outer)
                    .join(UserFavoritePool, isouter=True)  # noqa
            ).group_by(
                Pool.id,
                Pool.verbose_name,
                Pool.resource_pool_id,
                Pool.datapool_id,
                Pool.status,
                Pool.controller,
                Pool.keep_vms_on,
                Pool.free_vm_from_user,
                Pool.vm_action_upon_user_disconnect,
                Pool.vm_disconnect_action_timeout,
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
                AutomatedPool.enable_vms_remote_access,
                AutomatedPool.start_vms,
                AutomatedPool.set_vms_hostnames,
                AutomatedPool.include_vms_in_ad,
                AutomatedPool.ad_ou,
                RdsPool.id,
                Controller.address,
            )

            # take favorite pools only
            if user_id and get_favorite_only:
                query = query.where(UserFavoritePool.user_id == user_id)

            # Сортировка
            query = Pool.build_ordering(query, ordering)
        else:
            # Делаем пересечение только с основными таблицами
            query = query.select_from(
                Pool.join(AutomatedPool, isouter=True).join(RdsPool, isouter=True))

        return query

    @staticmethod
    async def soft_update_base_params(
        id, verbose_name, keep_vms_on, connection_types, creator, free_vm_from_user=False,
        vm_action_upon_user_disconnect=VmActionUponUserDisconnect.NONE,
        vm_disconnect_action_timeout=60
    ):
        old_pool_obj = await Pool.get(id)
        async with db.transaction():
            update_type, update_dict = await Pool.soft_update(
                id,
                verbose_name=verbose_name,
                keep_vms_on=keep_vms_on,
                free_vm_from_user=free_vm_from_user,
                connection_types=connection_types,
                creator=creator,
                vm_action_upon_user_disconnect=vm_action_upon_user_disconnect,
                vm_disconnect_action_timeout=vm_disconnect_action_timeout,
                updated=func.now()
            )

            msg = _local_("Pool {} has been updated.").format(old_pool_obj.verbose_name)
            creator = update_dict.pop("creator")
            desc = str(update_dict)
            await system_logger.info(
                msg, description=desc, user=creator, entity=update_type.entity
            )

            if old_pool_obj.tag and verbose_name:
                await update_type.tag_update(
                    tag=old_pool_obj.tag, verbose_name=verbose_name, creator=creator
                )

    @staticmethod
    async def get_pool(pool_id, ordering=None):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением.

        Возвращает данные со всех таблиц пулов. В идеале нужно сделать для фронта запрос общих для всех пулов данных и
        индивидуальные подробные запросы для каждого типа пулов
        """
        query = Pool.get_pools_query(ordering=ordering)
        query = query.where(Pool.id == pool_id)
        return await query.gino.first()

    @staticmethod
    async def get_pools(limit, offset, filters=None, ordering=None):
        """Такое построение запроса вызвано желанием иметь только 1 запрос с изначальным построением."""
        query = Pool.get_pools_query(ordering=ordering)
        if filters:
            query = query.where(and_(*filters))
        if not ordering:
            query = query.order_by(Pool.verbose_name)
        return await query.limit(limit).offset(offset).gino.all()

    async def get_vm_amount(self, only_free=False):
        """Нужно дорабатывать - отказаться от in и дублирования кода.

        :param only_free: учитываем только свободные VM
        :return: int
        Надо бы переделать это в статический метод а то везде приходится делать Pool.get(id)
        """
        if only_free:
            ero_query = EntityOwnerModel.select("entity_id").where(
                EntityOwnerModel.user_id != None  # noqa: E711
            )

            entity_query = EntityModel.select("entity_uuid").where(
                (EntityModel.entity_type == EntityType.VM)
                & (EntityModel.id.in_(ero_query))  # noqa: W503
            )

            vm_query = db.select([db.func.count()]).where(
                (VmModel.pool_id == self.id)
                & (VmModel.id.notin_(entity_query))  # noqa: W503
                & (VmModel.status == Status.ACTIVE)  # noqa: W503
            )

            return await vm_query.gino.scalar()

        return (
            await db.select([db.func.count()])
            .where(VmModel.pool_id == self.id)
            .gino.scalar()
        )

    def get_user_vms_query(self, user_id):
        """Формирует запрос всех ВМ пользователя с учетом его прав.

        Пользователь не может иметь больше одной машины в пуле -> комбинация pool_id и username уникальная.
        """
        # Список всех ВМ пользователя
        entity_query = EntityModel.select("entity_uuid").where(
            (EntityModel.entity_type == EntityType.VM)
            & (  # noqa: W503
                EntityModel.id.in_(
                    EntityOwnerModel.select("entity_id").where(
                        EntityOwnerModel.user_id == user_id
                    )
                )
            )
        )
        vm_query = VmModel.query.where(
            (VmModel.id.in_(entity_query)) & (VmModel.pool_id == self.id)
        )
        return vm_query

    async def get_vm(self, user_id):
        """Возвращает ВМ пользователя с учетом его прав.

        Сочетание pool id и username уникальное, т.к. пользователь не может иметь больше одной машины в пуле.
        """
        await system_logger.debug("Возвращаем ВМ пользователя")
        return await self.get_user_vms_query(user_id).gino.first()

    @property
    def assigned_groups_query(self):
        """Группы назначенные пулу."""
        query = EntityModel.query.where(
            (EntityModel.entity_type == EntityType.POOL)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        ).alias()
        return GroupModel.join(EntityOwnerModel.join(query).alias()).select()

    async def assigned_groups_paginator(self, limit, offset, ordering):
        query = self.assigned_groups_query
        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)
            query = (
                query.order_by(desc(ordering))
                if reverse
                else query.order_by(ordering)
            )
        return await query.limit(limit).offset(offset).gino.load(GroupModel).all()

    @property
    async def possible_groups(self):
        query = EntityModel.query.where(
            (EntityModel.entity_type == EntityType.POOL)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        ).alias()
        filtered_query = (
            GroupModel.join(EntityOwnerModel.join(query).alias(), isouter=True)
            .select()
            .where(text("anon_1.entity_owner_group_id is null"))
        )  # noqa
        return (
            await filtered_query.order_by(GroupModel.verbose_name)
            .gino.load(GroupModel)
            .all()
        )

    async def get_assigned_users_query(self):
        query = EntityModel.query.where(
            (EntityModel.entity_type == EntityType.POOL)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        ).alias()

        # Список администраторов системы
        admins_query_ids = await UserModel.get_superuser_ids_subquery()

        # Список явных пользователей
        users_query = EntityOwnerModel.join(query)
        user_query_ids = db.select([text("user_id")]).select_from(users_query)

        # Список пользователей состоящих в группах
        group_users_query = UserGroupModel.join(GroupModel).join(
            EntityOwnerModel.join(query)
        )
        group_users_ids = db.select([text("user_groups.user_id")]).select_from(
            group_users_query
        )

        # Список пользователей встречающихся в пересечении
        union_query = union_all(
            admins_query_ids, user_query_ids, group_users_ids
        ).alias("final_union_query")

        # Формирование заключительного списка пользователей
        finish_query = (
            UserModel.join(union_query, (UserModel.id == text("final_union_query.id")))
            .select()
            .group_by(UserModel.id)
        )
        # 5.05.2021 добавлено исключение "не активных" пользователей из итогового списка
        finish_query = finish_query.where(UserModel.is_active)
        return finish_query

    async def assigned_users_count(self):

        finish_query = await self.get_assigned_users_query()
        users_count = await db.select([db.func.count()]).select_from(finish_query.alias()).gino.scalar()
        return users_count

    async def assigned_users(self, ordering=None, limit=100, offset=0, username=None):
        """Пользователи назначенные пулу (с учетом групп)."""
        finish_query = await self.get_assigned_users_query()

        # filter by name pattern
        if username:
            finish_query = finish_query.where(UserModel.username.ilike(f"%{username}%"))

        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)
            finish_query = (
                finish_query.order_by(desc(ordering))
                if reverse
                else finish_query.order_by(ordering)
            )
        else:
            finish_query = finish_query.order_by(UserModel.username)
        return await finish_query.limit(limit).offset(offset).gino.all()

    async def check_if_user_assigned(self, user_id):
        assigned_users_query = await self.get_assigned_users_query()
        user = await assigned_users_query.where(UserModel.id == user_id).gino.first()
        return user

    async def get_possible_users_query(self):

        query = EntityModel.query.where(
            (EntityModel.entity_type == EntityType.POOL)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        ).alias()
        # Список пользователей состоящих в группах
        group_users_query = (
            UserGroupModel.join(GroupModel)
            .join(EntityOwnerModel.join(query).alias())
            .select()
            .alias("group_users_query")
        )
        group_users_ids = (
            db.select([text("group_users_query.user_id")]).select_from(group_users_query).alias("group_users_ids")
        )

        # Список явных пользователей
        users_query = EntityOwnerModel.join(query).select().alias("users_query")
        user_query_ids = (
            db.select([text("users_query.user_id")]).select_from(users_query).alias("user_query_ids")
        )

        # Список администраторов системы
        admins_query_ids = await UserModel.get_superuser_ids_subquery()
        admins_query_ids = admins_query_ids.alias("admins_query_ids")

        # Объединяем все три запроса и фильтруем активных пользователей
        # Outer join, потому что union_all что-то не взлетел
        finish_query = (
            UserModel.join(
                admins_query_ids, (UserModel.id == text("admins_query_ids.id")), isouter=True
            )
            .join(
                user_query_ids,
                (UserModel.id == text("user_query_ids.user_id")),  # noqa
                isouter=True,
            )
            .join(
            group_users_ids,  # noqa
            (UserModel.id == text("group_users_ids.user_id")),  # noqa
                isouter=True,
            )
            .select()
            .where(
                (
                    text("admins_query_ids.id is null")
                    & text("user_query_ids.user_id is null")  # noqa: W503
                    & text("group_users_ids.user_id is null")  # noqa: W503
                )
                & (UserModel.is_active)  # noqa: W503
            )
        )  # noqa
        return finish_query

    async def possible_users_count(self):

        finish_query = await self.get_possible_users_query()
        users_count = await db.select([db.func.count()]).select_from(finish_query.alias()).gino.scalar()
        return users_count

    async def possible_users(self, limit=100, offset=0, username=None):
        """Пользователи которых можно закрепить за пулом."""
        finish_query = await self.get_possible_users_query()

        # filter by name pattern
        if username:
            finish_query = finish_query.where(UserModel.username.ilike(f"%{username}%"))

        finish_query = finish_query.order_by(UserModel.username)
        return await finish_query.limit(limit).offset(offset).gino.load(UserModel).all()

    # ----- ----- ----- ----- ----- ----- -----

    async def add_user(self, user_id, creator):
        entity = await self.entity_obj
        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityOwnerModel.create(
                    entity_id=entity.id, user_id=user_id
                )
                user = await UserModel.get(user_id)
                await system_logger.info(
                    _local_("User {} has been included to pool {}.").format(
                        user.username, self.verbose_name
                    ),
                    user=creator,
                    entity=self.entity,
                )

                await self.notify_entitlement_changed(user_id=user_id)

        except UniqueViolationError:
            raise SimpleError(
                _local_("{} already has permission.").format(type(self).__name__),
                user=creator,
                entity=self.entity,
            )
        return ero

    async def remove_users(self, creator: str, users_list: list):
        # updated 17.12.2020
        entity = EntityModel.select("id").where(
            (EntityModel.entity_type == self.entity_type)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        )

        entitled_users = []
        for user_id in users_list:
            has_permission = await EntityOwnerModel.query.where(
                (EntityOwnerModel.user_id == user_id)
                & (EntityOwnerModel.entity_id == entity)  # noqa: W503
            ).gino.first()
            user = await UserModel.get(user_id)
            if has_permission:
                entitled_users.append(user_id)
                await system_logger.info(
                    _local_("Removing user {} from pool {}.").format(
                        user.username, self.verbose_name
                    ),
                    user=creator,
                    entity=self.entity,
                )
            else:
                await system_logger.warning(
                    _local_("User {} has no direct right to pool {}.").format(
                        user.username, self.verbose_name
                    ),
                    user=creator,
                    entity=self.entity,
                )

        # entity = EntityModel.select('id').where((EntityModel.entity_type == self.entity_type)
        # & (EntityModel.entity_uuid == self.id))

        operation_status = await EntityOwnerModel.delete.where(
            (EntityOwnerModel.user_id.in_(users_list))
            & (EntityOwnerModel.entity_id == entity)  # noqa: W503
        ).gino.status()

        for user_id in entitled_users:
            await self.notify_entitlement_changed(user_id=user_id)

        return operation_status

    async def add_group(self, group_id, creator):
        entity = await self.entity_obj

        try:
            async with db.transaction():
                if not entity:
                    entity = await EntityModel.create(**self.entity)
                ero = await EntityOwnerModel.create(
                    entity_id=entity.id, group_id=group_id
                )
                group = await GroupModel.get(group_id)
                await system_logger.info(
                    _local_("Group {} has been included to pool {}.").format(
                        group.verbose_name, self.verbose_name
                    ),
                    user=creator,
                    entity=self.entity,
                )

            await self.notify_entitlement_changed(group_id=group_id)

        except UniqueViolationError:
            raise SimpleError(
                _local_("Pool already has permission."), user=creator,
                entity=self.entity
            )
        return ero

    async def add_groups(self, creator, groups_list: list):
        for group_id in groups_list:
            await self.add_group(group_id, creator)
        return True

    async def remove_groups(self, creator, groups_list: list):
        for group_id in groups_list:
            group = await GroupModel.get(group_id)
            await system_logger.info(
                _local_("Removing group {} from pool {}.").format(
                    group.verbose_name, self.verbose_name
                ),
                user=creator,
                entity=self.entity,
            )
        entity = EntityModel.select("id").where(
            (EntityModel.entity_type == self.entity_type)
            & (EntityModel.entity_uuid == self.id)  # noqa: W503
        )
        ret = await EntityOwnerModel.delete.where(
            (EntityOwnerModel.group_id.in_(groups_list))
            & (EntityOwnerModel.entity_id == entity)  # noqa: W503
        ).gino.status()

        for group_id in groups_list:
            await self.notify_entitlement_changed(group_id=group_id)

        return ret

    async def free_assigned_vms(self, users_list: list):
        """Будут удалены все записи из EntityOwner соответствующие условию.

        Запрос такой ублюдский, потому что через Join в текущей версии Gino получалось очень много подзапросов.
        :param users_list: uuid пользователей для которых выполняется поиск
        :return: gino.status()
        """
        entity_query = EntityModel.select("id").where(
            (EntityModel.entity_type == EntityType.VM)
            & (  # noqa: W503
                EntityModel.entity_uuid.in_(
                    VmModel.select("id").where(VmModel.pool_id == self.id)
                )
            )
        )

        ero_query = EntityOwnerModel.delete.where(
            EntityOwnerModel.entity_id.in_(entity_query)
            & EntityOwnerModel.user_id.in_(users_list)  # noqa: W503
        )

        return await ero_query.gino.status()

    @classmethod
    async def create(
        cls, verbose_name, resource_pool_id, controller_id,
        connection_types, tag, pool_type, vm_action_upon_user_disconnect, vm_disconnect_action_timeout,
        creator, datapool_id=None
    ):
        if not controller_id:
            raise ValidationError(
                _local_("Controller {} not found.").format(controller_id))

        pool = await super().create(
            verbose_name=verbose_name,
            resource_pool_id=resource_pool_id,
            datapool_id=datapool_id,
            controller=controller_id,
            status=Status.CREATING,
            connection_types=connection_types,
            tag=tag,
            pool_type=pool_type,
            vm_action_upon_user_disconnect=vm_action_upon_user_disconnect,
            vm_disconnect_action_timeout=vm_disconnect_action_timeout,
            creator=creator
        )

        # Оповещаем о создании пула
        additional_data = await pool.additional_model_to_json_data()
        await publish_data_in_internal_channel(pool.get_resource_type(), WsEventToClient.CREATED.value,
                                               pool, additional_data)

        return pool

    async def full_delete(self, deleting_computers_from_ad_enabled=False, creator="system"):
        """Удаление сущности с удалением зависимых сущностей."""
        old_status = self.status  # Запомнить текущий статус
        controller_obj = await self.controller_obj
        controller_client = controller_obj.veil_client
        try:
            await self.set_status(Status.DELETING)

            automated_pool = await AutomatedPool.get(self.id)

            if automated_pool:
                if automated_pool.is_guest:
                    await system_logger.debug(
                        _local_("Delete VMs for GuestPool {}.").format(
                            self.verbose_name)
                    )
                else:
                    await system_logger.debug(
                        _local_("Delete VMs for AutomatedPool {}.").format(
                            self.verbose_name)
                    )
                vm_ids = await VmModel.get_vms_ids_in_pool(self.id)
                for vm_id in vm_ids:
                    vm = await VmModel.get(vm_id)
                    await system_logger.info(
                        _local_("VM {} has been removed from ECP VeiL.").format(
                            vm.verbose_name
                        ),
                        entity=vm.entity,
                    )

                remove_from_ecp = True
            else:
                vm_ids = await VmModel.get_vms_ids_in_pool(self.id)
                remove_from_ecp = False

            await VmModel.step_by_step_removing(controller_client=controller_client,
                                                vms_ids=vm_ids,
                                                creator=creator,
                                                remove_from_ecp=remove_from_ecp,
                                                deleting_computers_from_ad_enabled=deleting_computers_from_ad_enabled)

            if self.tag:
                await self.tag_remove(self.tag)

            await self.delete()
            msg = _local_(
                "Complete removal pool of desktops {verbose_name} is done.").format(
                verbose_name=self.verbose_name
            )
            await system_logger.info(msg, entity=self.entity, user=creator)

        except Exception:
            # Если возникло исключение во время удаления то возвращаем пред. статус
            await self.set_status(old_status)
            raise

        # Оповещаем об удалении пула
        additional_data = await self.additional_model_to_json_data()
        await publish_data_in_internal_channel(self.get_resource_type(),
                                               WsEventToClient.DELETED.value,
                                               self, additional_data)
        return True

    async def notify_entitlement_changed(self, user_id=None, group_id=None):
        additional_data = dict(user_id=str(user_id), group_id=str(group_id))
        await publish_data_in_internal_channel(self.get_resource_type(),
                                               WsEventToClient.POOL_ENTITLEMENT_CHANGED.value,
                                               self, additional_data)

    @classmethod
    async def activate(cls, pool_id, creator="system"):
        pool = await Pool.get(pool_id)
        await pool.set_status(Status.ACTIVE)
        entity = {"entity_type": EntityType.POOL, "entity_uuid": pool_id}
        # Активация ВМ. Добавлено 02.11.2020 - не факт, что нужно.
        # 16.03.2021 Нужно для подорожника
        vms = await VmModel.query.where(VmModel.pool_id == pool_id).gino.all()
        for vm in vms:
            if vm.status != Status.RESERVED:
                await vm.update(status=Status.ACTIVE).apply()
        await system_logger.info(
            _local_("Pool {} has been activated.").format(pool.verbose_name),
            entity=entity, user=creator
        )
        return True

    @classmethod
    async def deactivate(cls, pool_id, status=Status.FAILED):
        pool = await Pool.get(pool_id)
        if status != pool.status.name:
            await pool.set_status(status)
        entity = {"entity_type": EntityType.POOL, "entity_uuid": pool_id}
        if status == Status.FAILED:
            vms = await VmModel.query.where(VmModel.pool_id == pool_id).gino.all()
            for vm in vms:
                if vm.status != Status.RESERVED:
                    await vm.update(status=Status.FAILED).apply()
        await system_logger.warning(
            _local_("Pool {} status changed to {}.").format(pool.verbose_name,
                                                            status.value),
            entity=entity,
        )
        return True

    @classmethod
    async def enable(cls, pool_id):
        """Отличается от activate тем, что проверяет предыдущий статус."""
        pool = await Pool.get(pool_id)
        # Т.к. сейчас нет возможности остановить создание пула - не трогаем не активные
        if (pool.status == Status.FAILED) or (pool.status == Status.SERVICE):
            return await pool.activate(pool.id)
        return False

    async def get_free_vm_v2(self):
        """Возвращает `ближайшую` свободную ВМ.

        Поиск ближайшей:
        1. Формируем список ВСЕХ `АКТИВНЫХ` и `СВОБОДНЫХ` ВМ пула
        2. Получить от ECP VeiL список ВСЕХ `ВКЛЮЧЕННЫХ` ВМ на данном пуле ресурсов
        3. Отфильтровать полученный список оставив ВМ с п. 1
        4. Поиск ВМ среди п.3 у которой доступен гостевой агент
        5. Если гостевой агент нигде не отвечает - из пункта 3 беру первую включенную
        """
        # Список свободных ВМ (п.1)
        await system_logger.debug("Список свободных ВМ (п.1)")
        vm_ids = await VmModel.get_free_vms_ids(pool_id=self.id)
        if not vm_ids:
            return

        # Получаем список ВМ от ECP VeiL (п.2)
        await system_logger.debug("Получаем список ВМ от ECP VeiL (п.2)")
        pool_controller = await self.controller_obj
        controller_client = pool_controller.veil_client
        if not controller_client:
            return await VmModel.get(vm_ids[0])

        domain_client = controller_client.domain(resource_pool=self.resource_pool_id)
        domains_response = await domain_client.list(fields=["id", "guest_utils"],
                                                    params={"power_state": "ON"})

        # Берем первую свободную если не достучались до контроллера
        if not domains_response.success:
            vm = await VmModel.get(vm_ids[0])
            await system_logger.debug(
                "Не удалось найти подходящую ВМ. Возвращаем первую свободную {}.".format(vm.verbose_name))
            return await vm

        # Фильтруем ВМ пула (п.3)
        await system_logger.debug("Фильтруем ВМ пула (п.3)")
        veil_domains_list = domains_response.response
        filtered_domains = list()
        for domain in veil_domains_list:
            if domain.api_object_id in vm_ids:
                filtered_domains.append(domain)
        if not filtered_domains:
            return await VmModel.get(vm_ids[0])

        # Ищем среди ВМ ту, у которой доступен гостевой агент (п.4)
        await system_logger.debug(
            "Ищем среди ВМ ту, у которой доступен гостевой агент (п.4)")
        domain_enabled_qemu_id = await self.get_vm_with_enabled_qemu(
            domains=filtered_domains)
        await system_logger.debug(
            "ENABLED GUEST AGENT ID:{}".format(domain_enabled_qemu_id))
        if domain_enabled_qemu_id:
            return await VmModel.get(domain_enabled_qemu_id)

        # Берем первую включенную ВМ (п.5)
        await system_logger.debug("Берем первую включенную ВМ (п.5)")
        first_powered_domain = filtered_domains[0]
        return await VmModel.get(first_powered_domain.api_object_id)

    @staticmethod
    async def get_vm_with_enabled_qemu(domains: list):
        """Попытка найти включенную ВМ с активным гостевым агентом."""
        for domain in domains:
            if domain.qemu_state and domain.api_object_id:
                return domain.api_object_id

    async def get_vms_info(self, limit=500, offset=0, ordering=None, verbose_name=None):
        """Возвращает информацию для всех ВМ в пуле."""
        from web_app.pool.schema import VmType  # todo: это плохо. Common не должен зависеть от производного
        # Перенести этот метод в схему либо вернуть отсюда vms_list

        # Получаем список ВМ
        vms = await self.get_vms(limit=limit, offset=offset, verbose_name=verbose_name)

        if not vms:
            return
        # Получаем набор уникальных ids ВМ
        vm_ids = set(str(vm.id) for vm in vms)
        ids_str = ",".join(vm_ids)
        pool_controller = await self.controller_obj

        ids_str_list = wrap(ids_str, width=VEIL_MAX_IDS_LEN)

        # Получаем данные для каждого блока id
        vms_list = list()
        for ids_str_section in ids_str_list:
            # Запрашиваем на ECP VeiL данные
            fields = [
                "id",
                "user_power_state",
                "parent",
                "status",
                "guest_utils",
                "node",
            ]
            controller_client = pool_controller.veil_client
            if not controller_client:
                break
            domains_list_response = await controller_client.domain().list(
                fields=fields, params={"ids": ids_str_section}
            )
            vms_list += domains_list_response.paginator_results

        vms_dict = dict()
        for vm_info in vms_list:
            vm_info["parent_name"] = None
            # Получаем имя шаблона
            if vm_info["parent"]:
                vm_info["parent_name"] = vm_info["parent"]["verbose_name"]
            del vm_info["parent"]
            vms_dict[vm_info["id"]] = vm_info

        vms_info = list()
        qemu_state = None
        vms_list = list()

        for vm in vms:
            user_power_state = VmState.UNDEFINED
            vm_status = (
                Status.FAILED
            )  # Если с вейла не пришла инфа, то вм считается в статусе FAILED
            parent_name = None
            node = None
            for vm_id in vms_dict.keys():
                if str(vm_id) == str(vm.id):
                    user_power_state = vms_dict[vm_id]["user_power_state"]
                    parent_name = vms_dict[vm_id]["parent_name"]
                    vm_status = Status(vms_dict[vm_id]["status"])
                    guest_utils = vms_dict[vm_id].get("guest_utils")
                    node = vms_dict[vm_id]["node"]
                    qemu_state = (
                        guest_utils.get("qemu_state", False) if guest_utils else False
                    )

            # update status
            if (vm.status != Status.RESERVED) and \
               (vm.status != Status.SERVICE) and \
               (vm.status != Status.DELETING):
                await vm.update(status=vm_status).apply()

            # Формируем список с информацией по каждой вм в пуле
            vm_dict = vm.__values__
            vm_dict["user_power_state"] = user_power_state
            vm_dict["parent_name"] = parent_name
            vm_dict["qemu_state"] = 3 if qemu_state else 1
            vm_dict["node"] = node
            vm_dict["controller"] = {"id": pool_controller.id}
            vm_dict["username"] = await vm.username
            vms_list.append(vm_dict)

        if ordering:
            (ordering, reverse) = extract_ordering_data(ordering)

            if ordering == "verbose_name":
                def sort_lam(vm):
                    return vm["verbose_name"] if vm["verbose_name"] else DEFAULT_NAME
            elif ordering == "user":
                def sort_lam(vm):
                    return vm["username"] if vm["username"] else DEFAULT_NAME
            elif ordering == "status":
                def sort_lam(vm):
                    return vm["status"].value if vm["status"] else Status.FAILED
            elif ordering == "qemu_state":
                def sort_lam(vm):
                    return vm["qemu_state"] if vm["qemu_state"] else 1
            elif ordering == "parent_name":
                def sort_lam(vm):
                    return vm["parent_name"] if vm["parent_name"] else DEFAULT_NAME
            else:
                raise SimpleError(_local_("The sort parameter is incorrect."))
            vms_list = sorted(vms_list, key=sort_lam, reverse=reverse)

        for vm_info in vms_list:
            vms_info.append(VmType(**vm_info))
        return vms_info

    async def remove_vms(self, vm_ids, creator="system"):
        """Перенесенный метод из схемы и модели ВМ."""
        if not vm_ids:
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            raise SimpleError(_local_("List of VM should not be empty."), entity=entity)

        # get automated pool object
        automated_pool = await AutomatedPool.get(self.id)
        # get tag verbose name
        tag_must_be_detached = self.tag and not automated_pool
        # vms check
        # get list of vms ids which are in pool_id
        vms_ids_in_pool = await VmModel.get_vms_ids_in_pool(self.id)
        # delete tag for every domain in static_pool
        vms_list = list()
        for vm_id in vm_ids:
            # check if given vm_ids not in vms_ids_in_pool
            vm_not_in_the_pool = str(vm_id) not in vms_ids_in_pool
            if vm_not_in_the_pool:
                entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
                raise SimpleError(
                    _local_("VM doesn't belong to specified pool."),
                    description=str(vm_id),
                    entity=entity,
                )
            vm = await VmModel.get(vm_id)
            await vm.update(status=Status.DELETING).apply()
            if vm:
                vms_list.append(vm)

            if automated_pool:
                msg = _local_(
                    "VM {} has been removed from the pool {} and ECP VeiL.").format(
                    vm.verbose_name, self.verbose_name
                )
            else:
                msg = _local_("VM {} has been removed from the pool {}.").format(
                    vm.verbose_name, self.verbose_name
                )
            await system_logger.info(msg, entity=vm.entity, user=creator)
        # Remove tag for every VM
        if tag_must_be_detached and vms_list:
            await self.tag_remove_entities(tag=self.tag, vm_objects=vms_list)

    async def free_user_vms(self, user_id):
        """Освобождение ВМ от пользователя user_id."""
        vms_query = VmModel.select("id").where(VmModel.pool_id == self.id)
        entity_query = EntityModel.select("id").where(
            (EntityModel.entity_type == EntityType.VM)
            & (EntityModel.entity_uuid.in_(vms_query))  # noqa: W503
        )
        # Закоментировано резервирование, так как оно идет в противоречие с возможностью владения
        # машиной множеством пользователей
        # exists_count = (
        #     await db.select([db.func.count()])
        #     .where(
        #         (EntityOwnerModel.user_id == user_id)
        #         & (EntityOwnerModel.entity_id.in_(entity_query))  # noqa: W503
        #     )
        #     .gino.scalar()
        # )
        # if exists_count > 0:
        #     role_owner_query = EntityOwnerModel.select("entity_id").where(
        #         (EntityOwnerModel.user_id == user_id)
        #         & (EntityOwnerModel.entity_id.in_(entity_query))  # noqa: W503
        #     )
        #     exists_vm_query = EntityModel.select("entity_uuid").where(
        #         EntityModel.id.in_(role_owner_query)
        #     )
        #     await VmModel.update.values(status=Status.RESERVED).where(
        #         VmModel.id.in_(exists_vm_query)
        #     ).gino.status()
        ero_query = EntityOwnerModel.delete.where(
            (EntityOwnerModel.user_id == user_id)
            & (EntityOwnerModel.entity_id.in_(entity_query))  # noqa: W503
        )

        return await ero_query.gino.status()

    # override
    def get_resource_type(self):
        return POOLS_SUBSCRIPTION

    async def get_tag(self, tag):
        controller_obj = await self.controller_obj
        controller_client = controller_obj.veil_client
        tag_response = await controller_client.tag(str(tag)).info()
        return tag_response.response[0]

    @staticmethod
    async def tag_create(controller, verbose_name, creator):
        pool_tag = TagConfiguration(
            verbose_name=verbose_name, colour=Pool.pool_tag_colour()
        )
        controller_client = controller.veil_client
        # Попытки повтора заблокированы намеренно
        tag_response = await controller_client.tag(
            retry_opts=VeilRetryConfiguration()
        ).create(pool_tag)
        errors = tag_response.errors
        if tag_response.success:
            task = tag_response.task
            tag = task.first_entity if tag_response.task else None
            entity = {"entity_type": EntityType.POOL, "entity_uuid": None}
            await system_logger.info(
                _local_("Tag {name} created for pool {name}.").format(
                    name=verbose_name),
                user=creator,
                entity=entity,
            )
            return tag
        elif isinstance(errors, list) and errors[0].get("verbose_name"):
            response = await controller_client.tag(
                retry_opts=VeilRetryConfiguration()
            ).list(name=verbose_name)
            existing_name = response.response[0].verbose_name
            if existing_name == verbose_name:
                tag = response.response[0].api_object_id
                return tag

    async def tag_remove(self, tag):
        pool_tag = await self.get_tag(tag)
        remove_response = await pool_tag.remove()
        if remove_response.success:
            await system_logger.info(
                _local_("Tag {} removed from ECP VeiL.").format(pool_tag.verbose_name),
                user="system",
                entity=self.entity,
            )
        return remove_response.success

    async def tag_update(self, tag, verbose_name, creator):
        pool_tag = await self.get_tag(tag)
        update_response = await pool_tag.update(verbose_name=verbose_name)
        if update_response.success:
            await system_logger.info(
                _local_(
                    "Tag {name} updated for pool {name} and all vms in pool.").format(
                    name=verbose_name
                ),
                user=creator,
                entity=self.entity,
            )
        return update_response.success

    async def tag_remove_entity(self, tag, entity_id):
        pool_tag = await self.get_tag(tag)
        entity = VeilEntityConfiguration(
            entity_uuid=str(entity_id), entity_class="domain"
        )
        entity_response = await pool_tag.remove_entity(entity_configuration=entity)
        return entity_response.success

    async def tag_remove_entities(self, tag: str, vm_objects: list):
        """Remove 1 tag from many entities."""
        pool_tag = await self.get_tag(tag)
        ent_list = [
            VeilEntityConfiguration(entity_uuid=vm.id, entity_class="domain")
            for vm in vm_objects
        ]
        entity_response = await pool_tag.remove_entities(entities_conf=ent_list)
        if entity_response.success:
            for vm in vm_objects:
                await system_logger.info(
                    _local_("Tag {} removed from VM {}.").format(
                        pool_tag.verbose_name, vm.verbose_name
                    ),
                    user="system",
                    entity=vm.entity,
                )
        return entity_response.success

    async def tag_add_entity(self, tag, entity_id, verbose_name):
        pool_tag = await self.get_tag(tag)
        entity = VeilEntityConfiguration(entity_uuid=entity_id, entity_class="domain")
        entity_response = await pool_tag.add_entity(entity_configuration=entity)
        if entity_response.success:
            entity = {"entity_type": EntityType.VM, "entity_uuid": None}
            await system_logger.info(
                _local_("Tag {} added to VM {}.").format(pool_tag.verbose_name,
                                                         verbose_name),
                user="system",
                entity=entity,
            )
        return entity_response.success

    async def tag_add_entities(self, tag: str, vm_objects: list, creator: str = "system"):
        """Attach 1 tag to many entities."""
        pool_tag = await self.get_tag(tag)
        ent_list = [
            VeilEntityConfiguration(entity_uuid=vm.id, entity_class="domain")
            for vm in vm_objects
        ]
        entity_response = await pool_tag.add_entities(entities_conf=ent_list)
        if entity_response.success:
            for vm in vm_objects:
                await system_logger.info(
                    _local_("Tag {} added to VM {}.").format(
                        pool_tag.verbose_name, vm.verbose_name
                    ),
                    user=creator,
                    entity=vm.entity,
                )
        return entity_response.success

    async def backup_vms(self, creator="system"):
        vms = await self.get_vms()

        backup_response = await asyncio.gather(
            *[vm_object.backup(creator) for vm_object in vms], return_exceptions=True
        )
        for response in backup_response:
            if isinstance(response, ValueError):
                await system_logger.error(
                    str(response), user="system", entity=self.entity
                )

        return True


class RdsPool(db.Model):
    __tablename__ = "rds_pool"
    id = db.Column(
        UUID(),
        db.ForeignKey("pool.id", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
    )

    @property
    def entity_type(self):
        return EntityType.POOL

    @property
    def entity(self):
        return {"entity_type": self.entity_type, "entity_uuid": self.id}

    @classmethod
    async def soft_update(
        cls, id, verbose_name, keep_vms_on, connection_types, creator
    ):
        await Pool.soft_update_base_params(id, verbose_name, keep_vms_on,
                                           connection_types, creator)
        return True

    @classmethod
    async def soft_create(cls, creator, controller_id, resource_pool_id, veil_vm_data,
                          connection_types, verbose_name):

        async with db.transaction():
            # Создаем пул
            base_pool = await Pool.create(
                verbose_name=verbose_name,
                resource_pool_id=resource_pool_id,
                tag=None,
                controller_id=controller_id,
                connection_types=connection_types,
                pool_type=Pool.PoolTypes.RDS,
                vm_action_upon_user_disconnect=VmActionUponUserDisconnect.NONE,
                vm_disconnect_action_timeout=0,
                creator=creator
            )
            pool = await super().create(id=base_pool.id)

            for vm_type in veil_vm_data:
                await VmModel.create(
                    id=vm_type.id,
                    verbose_name=vm_type.verbose_name,
                    pool_id=pool.id,
                    template_id=None,
                    created_by_vdi=False,
                )

            # log
            await system_logger.info(
                _local_("RDS pool {} created.").format(verbose_name),
                user=creator,
                entity=pool.entity,
            )

            await pool.activate()
        return pool

    @staticmethod
    def get_supported_conn_types():
        return [Pool.PoolConnectionTypes.RDP.name,
                Pool.PoolConnectionTypes.NATIVE_RDP.name]

    @staticmethod
    async def get_farm_list(vm, user_name):
        """Получить с RDS Сервера список коллекций приложений, которые доступны пользователю.

        Приложение доступно, если оно опубликовано на ферме и у юзера есть право на пользование фермой.
        Запускаемый скрипт проходится по всем фермам, смотрит доступны ли они указанному юзеру,
        забирает списки приложений
        """
        veil_domain_client = await vm.vm_client

        qemu_guest_command = {"path": "wscript.exe",
                              "arg": [VEIL_GUEST_AGENT_WIN_PATH + "vbs.vbs",
                                      VEIL_GUEST_AGENT_WIN_PATH + "get_published_apps.ps1",
                                      user_name,
                                      "//B",
                                      "//NoLogo"],
                              "capture-output": True}

        stdout_farms_data = ""
        try:
            response = await veil_domain_client.guest_command(qemu_cmd="guest-exec",
                                                              f_args=qemu_guest_command,
                                                              timeout=55)
            # Ошибка запуска скриптка
            if response.status_code == 400:
                errors = response.data["errors"]
                raise RuntimeError(errors)

            # ошибки выполнения скрипта
            stderr_farms_data = response.data["guest-exec"].get("err-data")
            if stderr_farms_data:
                stderr_farms_data = stderr_farms_data.strip()
                stderr_farms_data = stderr_farms_data.strip("\r\n")
                if stderr_farms_data:
                    raise RuntimeError(stderr_farms_data)

            stdout_farms_data = response.data["guest-exec"]["out-data"]
            farm_data_dict = json.loads(stdout_farms_data)
            farm_list = farm_data_dict["farmlist"]
            return farm_list
        except JSONDecodeError:
            raise RuntimeError("Cant decode json. {}".format(stdout_farms_data))
        except asyncio.TimeoutError:
            raise RuntimeError("Timeout. Applications request took too long.")

    async def activate(self):
        return await Pool.activate(self.id)


class StaticPool(db.Model):
    """На данный момент отсутствует смысловая валидация на уровне таблиц (она в схемах)."""

    __tablename__ = "static_pool"
    id = db.Column(
        UUID(),
        db.ForeignKey("pool.id", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
    )

    @property
    def entity_type(self):
        return EntityType.POOL

    @property
    def entity(self):
        return {"entity_type": self.entity_type, "entity_uuid": self.id}

    @classmethod
    async def soft_create(
        cls,
        creator,
        veil_vm_data: list,
        verbose_name: str,
        tag: str,
        controller_id,
        resource_pool_id: str,
        connection_types: list,
        vm_action_upon_user_disconnect,
        vm_disconnect_action_timeout,
    ):
        """Nested transactions are atomic."""
        async with db.transaction():
            # Создаем пул
            pl = await Pool.create(
                verbose_name=verbose_name,
                controller_id=controller_id,
                resource_pool_id=resource_pool_id,
                connection_types=connection_types,
                tag=tag,
                pool_type=Pool.PoolTypes.STATIC,
                vm_action_upon_user_disconnect=vm_action_upon_user_disconnect,
                vm_disconnect_action_timeout=vm_disconnect_action_timeout,
                creator=creator
            )
            pool = await super().create(id=pl.id)
            # Создаем ВМ
            vm_obj_list = list()
            for vm_type in veil_vm_data:
                vm = await VmModel.create(
                    id=vm_type.id,
                    verbose_name=vm_type.verbose_name,
                    pool_id=pool.id,
                    template_id=None,
                    created_by_vdi=False,
                )
                vm_obj_list.append(vm)
                await system_logger.debug(
                    _local_("VM {} created.").format(vm_type.verbose_name)
                )

                msg = _local_("VM {} created.").format(vm.verbose_name)
                description = _local_("VM {} created and added to the pool {}.").format(
                    vm.verbose_name, verbose_name
                )
                await system_logger.info(
                    message=msg, description=description, entity=vm.entity
                )
            # Разом добавляем теги для всех ВМ
            if tag and vm_obj_list:
                await pl.tag_add_entities(tag=tag, vm_objects=vm_obj_list)
            # Записываем в лог успех
            await system_logger.info(
                _local_("Static pool {} created.").format(verbose_name),
                user=creator,
                entity=pool.entity,
            )
            # Активируем созданный пул
            await pool.activate()
        return pool

    @classmethod
    async def soft_update(
        cls, id, verbose_name, keep_vms_on, free_vm_from_user, connection_types,
        creator, vm_action_upon_user_disconnect, vm_disconnect_action_timeout
    ):
        await Pool.soft_update_base_params(id, verbose_name, keep_vms_on, connection_types, creator,
                                           free_vm_from_user, vm_action_upon_user_disconnect,
                                           vm_disconnect_action_timeout)
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

    __tablename__ = "automated_pool"

    id = db.Column(
        UUID(),
        db.ForeignKey("pool.id", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
    )
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
    enable_vms_remote_access = db.Column(db.Boolean(), nullable=False, default=True)
    start_vms = db.Column(db.Boolean(), nullable=False, default=True)
    set_vms_hostnames = db.Column(db.Boolean(), nullable=False, default=False)
    include_vms_in_ad = db.Column(db.Boolean(), nullable=False, default=False)
    # Группы/Контейнеры в Active Directory для назначения виртуальным машинам пула
    ad_ou = db.Column(db.Unicode(length=1000), nullable=True)
    is_guest = db.Column(db.Boolean(), nullable=False, default=False)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties:

    @property
    def entity_type(self):
        return EntityType.POOL

    @property
    def entity(self):
        return {"entity_type": self.entity_type, "entity_uuid": self.id}

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
    async def resource_pool_id(self):
        pool = await Pool.get(self.id)
        if pool:
            return pool.resource_pool_id

    @property
    async def datapool_id(self):
        pool = await Pool.get(self.id)
        if pool:
            return pool.datapool_id

    @property
    async def keep_vms_on(self):
        pool = await Pool.get(self.id)
        if pool:
            return pool.keep_vms_on

    @property
    async def free_vm_from_user(self):
        pool = await Pool.get(self.id)
        if pool:
            return pool.free_vm_from_user

    # ----- ----- ----- ----- ----- ----- -----

    async def activate(self):
        return await Pool.activate(self.id)

    async def deactivate(self, status=Status.FAILED):
        return await Pool.deactivate(self.id, status=status)

    @classmethod
    async def soft_create(
        cls,
        creator,
        verbose_name,
        controller_id,
        resource_pool_id,
        datapool_id,
        template_id,
        increase_step,
        initial_size,
        reserve_size,
        total_size,
        vm_name_template,
        create_thin_clones,
        enable_vms_remote_access,
        start_vms,
        set_vms_hostnames,
        include_vms_in_ad,
        connection_types,
        tag,
        vm_action_upon_user_disconnect,
        vm_disconnect_action_timeout,
        ad_ou: str = None,
        is_guest: bool = False
    ):
        """Nested transactions are atomic."""
        current_pool_type = Pool.PoolTypes.GUEST if is_guest else Pool.PoolTypes.AUTOMATED
        async with db.transaction():
            # Создаем базовую сущность Pool
            pool = await Pool.create(
                verbose_name=verbose_name,
                resource_pool_id=resource_pool_id,
                datapool_id=datapool_id,
                controller_id=controller_id,
                connection_types=connection_types,
                tag=tag,
                pool_type=current_pool_type,
                vm_action_upon_user_disconnect=vm_action_upon_user_disconnect,
                vm_disconnect_action_timeout=vm_disconnect_action_timeout,
                creator=creator
            )
            # Создаем AutomatedPool
            automated_pool = await super().create(
                id=pool.id,
                template_id=template_id,
                increase_step=increase_step,
                max_amount_of_create_attempts=POOL_MAX_CREATE_ATTEMPTS,
                initial_size=initial_size,
                reserve_size=reserve_size,
                total_size=total_size,
                vm_name_template=vm_name_template,
                create_thin_clones=create_thin_clones,
                enable_vms_remote_access=enable_vms_remote_access,
                start_vms=start_vms,
                set_vms_hostnames=set_vms_hostnames,
                include_vms_in_ad=include_vms_in_ad,
                ad_ou=ad_ou,
                is_guest=is_guest
            )
            # Записываем событие в журнал
            description = _local_(
                "Initial_size: {}, total_size: {}, increase_step {}, reserve_size {}."
            ).format(initial_size, total_size, increase_step, reserve_size)
            if automated_pool.is_guest:
                await system_logger.info(
                    _local_("GuestPool {} is created.").format(verbose_name),
                    user=creator,
                    entity=pool.entity,
                    description=description,
                )
            else:
                await system_logger.info(
                    _local_("AutomatedPool {} is created.").format(verbose_name),
                    user=creator,
                    entity=pool.entity,
                    description=description,
                )

            return automated_pool

    async def soft_update(
        self,
        creator,
        verbose_name,
        reserve_size,
        total_size,
        increase_step,
        vm_name_template,
        keep_vms_on: bool,
        free_vm_from_user: bool,
        vm_action_upon_user_disconnect,
        vm_disconnect_action_timeout,
        create_thin_clones: bool,
        enable_vms_remote_access: bool,
        start_vms: bool,
        set_vms_hostnames: bool,
        include_vms_in_ad: bool,
        connection_types,
        ad_ou: str
    ):
        pool_kwargs = dict()
        auto_pool_kwargs = dict()
        old_pool_obj = await Pool.get(self.id)
        old_verbose_name = await self.verbose_name
        async with db.transaction():
            # Update Pool values
            if verbose_name:
                pool_kwargs["verbose_name"] = verbose_name
                if old_pool_obj.tag:
                    pool = await Pool.get(self.id)
                    await pool.tag_update(
                        tag=old_pool_obj.tag, verbose_name=verbose_name, creator=creator
                    )
            if isinstance(keep_vms_on, bool):
                pool_kwargs["keep_vms_on"] = keep_vms_on
            if isinstance(free_vm_from_user, bool):
                pool_kwargs["free_vm_from_user"] = free_vm_from_user
            if connection_types:
                pool_kwargs["connection_types"] = connection_types
            if vm_action_upon_user_disconnect:
                pool_kwargs["vm_action_upon_user_disconnect"] = vm_action_upon_user_disconnect
            if vm_disconnect_action_timeout:
                pool_kwargs["vm_disconnect_action_timeout"] = vm_disconnect_action_timeout
            if pool_kwargs:
                await system_logger.debug(
                    _local_("Update Pool {} values.").format(
                        await self.verbose_name
                    )
                )
                pool = await Pool.get(self.id)
                await pool.update(updated=func.now(), **pool_kwargs).apply()

            # Update AutomatedPool values
            if reserve_size:
                auto_pool_kwargs["reserve_size"] = reserve_size
            if total_size:
                auto_pool_kwargs["total_size"] = total_size
            if increase_step:
                auto_pool_kwargs["increase_step"] = increase_step
            if vm_name_template:
                auto_pool_kwargs["vm_name_template"] = vm_name_template
            if not ad_ou and isinstance(ad_ou, str):
                auto_pool_kwargs["ad_ou"] = None
            elif ad_ou:
                auto_pool_kwargs["ad_ou"] = ad_ou
            if isinstance(create_thin_clones, bool):
                auto_pool_kwargs["create_thin_clones"] = create_thin_clones
            if isinstance(enable_vms_remote_access, bool):
                auto_pool_kwargs["enable_vms_remote_access"] = enable_vms_remote_access
            if isinstance(start_vms, bool):
                auto_pool_kwargs["start_vms"] = start_vms
            if isinstance(set_vms_hostnames, bool):
                auto_pool_kwargs["set_vms_hostnames"] = set_vms_hostnames
            if isinstance(include_vms_in_ad, bool):
                auto_pool_kwargs["include_vms_in_ad"] = include_vms_in_ad
            if auto_pool_kwargs:
                desc = str(auto_pool_kwargs)
                await system_logger.debug(
                    _local_("Update Pool {} values.").format(
                        await self.verbose_name
                    ),
                    description=desc,
                    user=creator,
                    entity=self.entity,
                )
                await self.update(**auto_pool_kwargs).apply()
        # Событие о редакировании пула
        pool_kwargs.update(auto_pool_kwargs)
        msg = _local_("Pool {} has been updated.").format(old_verbose_name)
        await system_logger.info(
            message=msg, description=str(pool_kwargs), user=creator, entity=self.entity
        )

        return True

    async def process_failed_multitask(self, multitask_id: str):
        """Check multi-task`s subtasks status and return only good ids."""
        # prepare connection
        pool_controller = await self.controller_obj
        task_client = pool_controller.veil_client.task()
        # get all success subtasks
        sub_tasks = await task_client.list(
            parent=multitask_id,
            status=VeilApiObjectStatus.success,
            paginator=VeilRestPaginator(ordering="created", limit=10000),
            extra_params={"fields": "id,name,entities"},
        )
        # prepare conditions
        success_ids = list()
        creating_task_pattern = "Creating a virtual"
        thin_clones_pattern = "snapshot."
        # parse VeiL ECP response
        for task in sub_tasks.response:
            if (
                creating_task_pattern in task.name
                and task.name[-9:] != thin_clones_pattern  # noqa: W503
            ):
                for entity_id, entity_type in task.entities.items():
                    if entity_type == "domain":
                        success_ids.append(entity_id)
        # skip last domain in list
        if success_ids:
            success_ids.pop()
        return success_ids

    async def step_by_step_adding(self, count: int = 1) -> dict:
        """Блочное копирование ВМ на основе шаблона."""
        # Ответ содержит 2 ключа, для возможности частичного создания блока ВМ
        result = dict(vms_list=None, error=None)
        copied_vms_list = list()
        remaining_count = count

        # Для выставления процентов выполнения задачи
        approximate_steps_amount = count // DOMAIN_CREATION_MAX_STEP + 1
        percent_by_step = round(100 / approximate_steps_amount)
        current_percent = 0

        # Попытки создать ВМ c шагом DOMAIN_CREATION_MAX_STEP
        while remaining_count > 0:
            # Количество ВМ создаваемых за 1 раз
            if abs(remaining_count) > DOMAIN_CREATION_MAX_STEP:
                step_count = DOMAIN_CREATION_MAX_STEP
            else:
                step_count = abs(remaining_count)

            try:
                # Вызываем копирование ВМ
                copied_vms = await self.add_vm(count=step_count)
                copied_vms_list.extend(copied_vms)
            except (AssertionError, VmCreationError) as add_err:
                # прерываем выполнение при первом же Exception
                result["error"] = add_err
                return result
            finally:
                result["vms_list"] = copied_vms_list
            # Уменьшаем оставшееся количество ВМ
            remaining_count = remaining_count - DOMAIN_CREATION_MAX_STEP

            # Обновляем прогресс выполнения задачи
            current_percent += percent_by_step
            await Task.set_progress_to_task_associated_with_entity(self.id,
                                                                   current_percent)

        # Выполнение успешно
        return result

    async def add_vm(self, count: int = 1):
        """Try to add VM to pool."""
        pool_verbose_name = await self.verbose_name
        verbose_name = self.vm_name_template or pool_verbose_name
        pool_controller = await self.controller_obj
        # Прерываем выполнение при отсутствии клиента
        if not pool_controller.veil_client:
            raise AssertionError(
                _local_("There is no client for pool {}.").format(pool_verbose_name)
            )
        # Подбор имени выполняет VeiL ECP, но, если ВМ 1 - не будет присвоен индекс.
        if count == 1:
            verbose_name = "{name}-1".format(name=verbose_name)

        params = {
            "verbose_name": verbose_name,
            "domain_id": str(self.template_id),
            "resource_pool_id": str(await self.resource_pool_id),
            "datapool_id": await self.datapool_id,
            "controller_id": pool_controller.id,
            "create_thin_clones": self.create_thin_clones,
            "count": count,
        }
        vm_multi_task_id = None
        try:
            # Постановка задачи на создание (копирование) ВМ
            vm_info = await VmModel.copy(**params)

            # Ожидаем завершения таски создания ВМ
            vm_multi_task_id = vm_info["task_id"]
            pending_vm_ids = vm_info["ids"]

            task_completed = False
            task_client = pool_controller.veil_client.task(task_id=vm_multi_task_id)
            while task_client and not task_completed:
                await asyncio.sleep(VEIL_OPERATION_WAITING)
                task_completed = await task_client.is_finished()

            # Если задача выполнена с ошибкой - получаем успешные ВМ для дальнейшего создания
            if task_client:
                task_success = await task_client.is_success()
                api_object_id = task_client.api_object_id
            else:
                task_success = False
                api_object_id = ""
            if not task_success:
                success_vm_ids = await self.process_failed_multitask(vm_multi_task_id)
                await system_logger.warning(
                    message=_local_("VM creation task {} finished with error.").format(
                        api_object_id
                    )
                )
                await self.deactivate(status=Status.PARTIAL)
            else:
                success_vm_ids = pending_vm_ids
        except VmCreationError:
            # Исключение для прерывания повторных попыток создания заведомо провальных задач.
            await self.deactivate()
            raise
        except asyncio.CancelledError:
            await self.deactivate()
            # Если получили CancelledError в ходе ожидания создания вм,
            # то отменяем на контроллере таску создания вм.
            # (Например, при мягком завершении процесса pool_worker)
            try:
                if vm_multi_task_id:
                    task_client = pool_controller.veil_client.task(task_id=vm_multi_task_id)
                    await task_client.cancel()
            except Exception as ex:
                msg = _local_("Fail to cancel VM creation task.")
                entity = {"entity_type": EntityType.VM, "entity_uuid": None}
                await system_logger.debug(
                    message=msg, description=str(ex), entity=entity
                )
            raise

        vm_obj_list = list()
        # Получаем актуальное имя виртуальной машины присвоенное контроллером
        domain_connect = pool_controller.veil_client.domain()

        # Формируем исходный список ВМ
        ids_str = ",".join(pending_vm_ids)
        ids_str_list = wrap(ids_str, width=VEIL_MAX_IDS_LEN)
        # Получаем данные для каждого блока id
        for ids_str_section in ids_str_list:
            response = await domain_connect.list(
                fields=["verbose_name", "id"], params={"ids": ids_str_section}
            )
            if response.success:
                pool = await Pool.get(self.id)
                # Создаем ВМ
                for domain in response.response:
                    vm_status = (
                        Status.ACTIVE
                        if domain.api_object_id in success_vm_ids
                        else Status.FAILED
                    )
                    vm_object = await VmModel.create(
                        id=domain.api_object_id,
                        pool_id=str(self.id),
                        template_id=str(self.template_id),
                        created_by_vdi=True,
                        verbose_name=domain.verbose_name,
                        status=vm_status
                    )
                    vm_obj_list.append(vm_object)

                    msg = _local_("VM {} created.").format(vm_object.verbose_name)
                    description = _local_(
                        "VM {} created and added to the pool {}.").format(
                        vm_object.verbose_name, verbose_name
                    )
                    await system_logger.info(
                        message=msg, description=description, entity=vm_object.entity
                    )
                # Добавляем разом теги для созданных ВМ
                if pool.tag and vm_obj_list:
                    await pool.tag_add_entities(tag=pool.tag, vm_objects=vm_obj_list)

        # Логирование результата созданных ВМ (совпадение количества) происходит выше
        return vm_obj_list

    @property
    async def template_os_type(self):
        """Получает информацию об ОС шаблона от VeiL ECP."""
        pool_controller = await self.controller_obj
        if not pool_controller.veil_client:
            return
        veil_template = pool_controller.veil_client.domain(
            domain_id=str(self.template_id)
        )
        await veil_template.info()
        return veil_template.os_type

    async def add_initial_vms(self, creator="system"):
        """Create required initial amount of VMs for pool."""
        # Fetching template info from controller.
        verbose_name = await self.verbose_name
        pool_os_type = await self.template_os_type
        await self.update(os_type=pool_os_type).apply()

        pool = await Pool.get(self.id)

        # если инициализация пула была прервана -> в пуле уже могут быть ВМ
        num_of_vms_in_pool = await pool.get_vm_amount()

        # Добавлено 1.06.2021
        # Создание ВМ происходит блоками и неизвестно в какой момент произойдет ошибка
        # новый механизм не прокидывает исключение явно, но возвращает их в поле `error`
        required_amount_to_create = max(0, self.initial_size - num_of_vms_in_pool)
        if required_amount_to_create == 0:
            return

        creation_result = await self.step_by_step_adding(count=required_amount_to_create)
        creation_error = creation_result["error"]
        # Если создание было выполнено с ошибкой отличной от
        # VmCreationError -> прерываем выполнение

        if creation_error:
            # log that we can`t create required initial amount of VMs
            await system_logger.error(
                _local_("VM creation error."),
                entity=self.entity,
                description=str(creation_error),
                user=creator
            )

        # Непредусмотренные ошибки пройдены -> завершаем выполнение
        created_vms = creation_result["vms_list"]
        num_of_vms_in_pool += len(created_vms)
        await Task.set_progress_to_task_associated_with_entity(self.id, 100)

        creation_successful = self.initial_size <= num_of_vms_in_pool
        if creation_successful:
            msg = _local_("{} vm(s) are successfully added in the {} pool.").format(
                self.initial_size, verbose_name
            )
            await system_logger.info(msg, entity=self.entity, user=creator)
        else:
            msg = _local_("Adding VM to the pool {} finished with errors.").format(
                verbose_name
            )
            description = _local_("Required: {}, created: {}.").format(
                self.initial_size, num_of_vms_in_pool
            )
            await system_logger.error(
                message=msg, entity=self.entity, description=description, user=creator
            )
            # без исключения таска завершится с FINISHED а не FAILED
            raise PoolCreationError(msg)

    async def prepare_initial_vms(self, creator="system"):
        """Подготавливает ВМ для дальнейшего использования тонким клиентом."""
        vm_objects = await VmModel.query.where(VmModel.pool_id == self.id).gino.all()
        if not vm_objects:
            return
        active_directory_object = await AuthenticationDirectory.query.where(
            AuthenticationDirectory.status == Status.ACTIVE
        ).gino.first()

        results_future = await asyncio.gather(
            *[
                vm_object.prepare_with_timeout(
                    active_directory_object, self.ad_ou, self, creator
                )
                for vm_object in vm_objects
            ],
            return_exceptions=True
        )

        return results_future

    async def check_if_total_size_reached(self):

        pool = await Pool.get(self.id)
        vm_amount = await pool.get_vm_amount()
        return vm_amount >= self.total_size

    async def check_if_not_enough_free_vms(self):

        pool = await Pool.get(self.id)
        free_vm_amount = await pool.get_vm_amount(only_free=True)
        return free_vm_amount < self.reserve_size

    def preparation_required(self):
        return self.enable_vms_remote_access or self.start_vms or self.set_vms_hostnames or self.include_vms_in_ad


class UserFavoritePool(db.Model, AbstractSortableStatusModel):
    """Table of favorite pools."""

    __tablename__ = "user_favorite_pool"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "pool_id", name="user_id_pool_id_unique_constraint"
        ),
    )

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(), db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    pool_id = db.Column(UUID(), db.ForeignKey("pool.id", ondelete="CASCADE"), nullable=False)
