# -*- coding: utf-8 -*
import datetime
import json
import re
import uuid

from asyncpg.exceptions import UniqueViolationError

import pyotp

from sqlalchemy import Enum as AlchemyEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from veil_aio_au import VeilResult as VeilAuthResult

from common.database import db
from common.languages import _local_
from common.log.journal import system_logger
from common.models.settings import Settings
from common.models.user_tk_permission import (
    GroupTkPermission,
    TkPermission,
    UserTkPermission,
)
from common.settings import (
    PAM_AUTH, PAM_SUPERUSER_GROUP,
    PAM_USER_GROUP,
    REDIS_THIN_CLIENT_CMD_CHANNEL,
    SECRET_KEY
)
from common.veil.auth import hashers
from common.veil.auth.veil_pam import veil_auth_class
from common.veil.veil_errors import MeaningError, PamError, SilentError, SimpleError
from common.veil.veil_gino import (
    AbstractSortableStatusModel,
    EntityType,
    Role,
    VeilModel,
)
from common.veil.veil_redis import ThinClientCmd, publish_to_redis


class Entity(db.Model):
    """
    entity_type: тип сущности из Enum.

    entity_uuid: UUID сущности, если в качестве EntityType указано название таблицы.
    """

    __tablename__ = "entity"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_type = db.Column(
        AlchemyEnum(EntityType), nullable=False, index=True, default=EntityType.SYSTEM
    )
    entity_uuid = db.Column(UUID(), nullable=True, index=True)

    @classmethod
    async def create(cls, entity_uuid, entity_type):
        entity = await Entity.query.where(
            (Entity.entity_type == entity_type) & (Entity.entity_uuid == entity_uuid)
        ).gino.first()
        if not entity:
            entity = await super().create(
                entity_type=entity_type, entity_uuid=entity_uuid
            )
        return entity


class EntityOwner(db.Model):
    """Ограничение прав доступа к сущности для конкретного типа роли.

    Если user_id и group_id null, то ограничение доступа к сущности только по Роли
    Если role пустой, то только по пользователю.
    """

    __tablename__ = "entity_owner"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(), db.ForeignKey(Entity.id, ondelete="CASCADE"))
    user_id = db.Column(
        UUID(), db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )
    group_id = db.Column(
        UUID(), db.ForeignKey("group.id", ondelete="CASCADE"), nullable=True
    )

    @classmethod
    def get_occupied_vms(cls):
        """Формирует запрос возвращающий UUID занятых ВМ."""
        entity_query = Entity.select("entity_uuid").where(
            (Entity.entity_type == EntityType.VM)
            & (Entity.id.in_(cls.select("entity_id")))  # noqa: W503
        )
        return entity_query

    @classmethod
    async def multi_remove(cls, ids: list, entity_type: EntityType):
        """Групповое удаление прав владения."""
        # Преобразуем UUID в строки
        entity_ids_str = [str(entity_row) for entity_row in ids]
        # Определяем есть ли что удалять
        entity_q = Entity.select("id").where(
            (Entity.entity_type == entity_type)
            & (Entity.entity_uuid.in_(entity_ids_str))  # noqa: W503
        )
        has_ownership = await entity_q.gino.all()
        if has_ownership:
            return await cls.delete.where(cls.entity_id.in_(entity_q)).gino.status()
        return False


class User(AbstractSortableStatusModel, VeilModel):
    __tablename__ = "user"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
    password_expiration_date = db.Column(db.DateTime(timezone=True), nullable=True)
    email = db.Column(db.Unicode(length=256), unique=False, nullable=True)
    last_name = db.Column(db.Unicode(length=128))
    first_name = db.Column(db.Unicode(length=32))
    date_joined = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    last_login = db.Column(db.DateTime(timezone=True), server_default=func.now())
    is_superuser = db.Column(
        db.Boolean(), default=False
    )  # Атрибут локальной авторизации
    is_active = db.Column(db.Boolean(), default=True)
    two_factor = db.Column(db.Boolean(), default=False)  # 2fa
    secret = db.Column(db.Unicode(length=32), nullable=True)  # 2fa
    by_ad = db.Column(db.Boolean(), default=False)
    local_password = db.Column(db.Boolean(), default=True)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    def entity_type(self):
        return EntityType.USER

    async def superuser(self) -> bool:
        """Следует использовать вместо is_superuser attr."""
        if PAM_AUTH and not self.by_ad:
            return await self.pam_user_in_group(PAM_SUPERUSER_GROUP)
        else:
            return self.is_superuser

    @property
    async def assigned_groups(self):
        groups = (
            await Group.join(
                UserGroup.query.where(UserGroup.user_id == self.id).alias()
            )
            .select()
            .gino.load(Group)
            .all()
        )
        return groups

    @property
    async def assigned_groups_ids(self):
        groups = (
            await UserGroup.select("group_id")
            .where(UserGroup.user_id == self.id)
            .gino.all()
        )
        groups_ids_list = [group.group_id for group in groups]
        return groups_ids_list

    @property
    async def possible_groups(self):
        possible_groups_query = (
            Group.join(
                UserGroup.query.where(UserGroup.user_id == self.id).alias(),
                isouter=True,
            )
            .select()
            .where(text("anon_1.id is null"))
        )  # noqa
        return await possible_groups_query.gino.load(User).all()

    @property
    async def roles(self):
        is_superuser = await self.superuser()
        if is_superuser:
            all_roles_set = set(Role)  # noqa
            return all_roles_set

        user_roles = await UserRole.query.where(UserRole.user_id == self.id).gino.all()
        all_roles_list = [role_type.role for role_type in user_roles]

        user_groups = await self.assigned_groups
        for group in user_groups:
            group_roles = await group.roles
            all_roles_list += [role_type.role for role_type in group_roles]

        roles_set = set(all_roles_list)
        # Сейчас роли будут в случайном порядке.
        return roles_set

    async def pools(self, get_favorite_only=False):
        """Получить список пулов.

        get_favorite_only - вернуть ли только изранные пулы.
        """
        # Либо размещать staticmethod в пулах, либо импорт тут, либо хардкодить названия полей.
        from common.models.pool import Pool

        is_superuser = await self.superuser()
        if is_superuser:
            pools_query = Pool.get_pools_query(user_id=self.id,
                                               get_favorite_only=get_favorite_only,
                                               is_superuser=is_superuser)
        else:
            user_roles = await self.roles
            user_groups_ids = await self.assigned_groups_ids
            pools_query = Pool.get_pools_query(
                user_id=self.id, groups_ids_list=user_groups_ids,
                role_set=user_roles, get_favorite_only=get_favorite_only,
                is_superuser=is_superuser,
            )

        pools = await pools_query.gino.all()

        pools_list = [
            {
                "id": str(pool.master_id),
                "name": pool.verbose_name,
                "os_type": pool.os_type,
                "status": pool.status.value,
                "connection_types": [
                    connection_type.value for connection_type in pool.connection_types
                ],
                "favorite": pool.favorite,
            }
            for pool in pools
        ]

        return pools_list

    @staticmethod
    async def validate_username(username):
        # Валидация для синхронизации пользователей из AD
        if not username:
            raise SimpleError(_local_("username can`t be empty."))
        username_len = len(username)
        if 0 < username_len <= 128:
            return username
        if username_len > 128:
            raise SimpleError(_local_("username must be <= 128 characters."))
        username_re = re.compile("^[a-zA-Z][a-zA-Z0-9.-_+]$")
        template_name = re.match(username_re, username)
        if template_name:
            return username
        raise SimpleError(
            _local_(
                "username {} must contain letters, digits, _, +, begin from letter and can't contain any spaces.").format(
                username)
        )

    @staticmethod
    async def get_id(username):
        return await User.select("id").where(User.username == username).gino.scalar()

    @classmethod
    async def get_superuser_ids_subquery(cls):
        """Возвращает подзапрос формирующий id суперпользователей системы."""
        admins_query = cls.query.where(cls.is_superuser)
        # Если включена PAM, необходимо проверить наличие пользователей в системной группе
        if PAM_AUTH:
            superusers = await admins_query.gino.all()
            superuser_ids = set()
            for user in superusers:
                system_superuser = await user.superuser()
                if system_superuser:
                    superuser_ids.add(user.id)
            system_superuser_filter = cls.query.where(cls.id.in_(superuser_ids))
            return db.select([text("id")]).select_from(system_superuser_filter.alias())

        return db.select([text("id")]).select_from(admins_query.alias())

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    async def add_role(self, role, creator):
        try:
            await system_logger.info(
                _local_("Role {} is added to user {}.").format(role, self.username),
                user=creator,
                entity=self.entity,
            )
            add = await UserRole.create(user_id=self.id, role=role)
            user = await self.get(self.id)
            assigned_roles = await user.roles
            await system_logger.debug(
                _local_("User {} roles: {}.").format(user.username, assigned_roles)
            )
            return add
        except UniqueViolationError:
            raise SimpleError(
                _local_("Role {} is assigned to user {}.").format(role, self.id),
                user=creator
            )

    async def remove_roles(self, roles_list=None, creator="system"):
        if not roles_list:
            return await UserRole.delete.where(
                UserRole.user_id == self.id
            ).gino.status()
        if roles_list and isinstance(roles_list, list):
            role_del = " ".join(roles_list)
            await system_logger.info(
                _local_("Roles: {} was deleted to user {}.").format(role_del,
                                                                    self.username),
                user=creator,
                entity=self.entity,
            )
            remove = await UserRole.delete.where(
                (UserRole.role.in_(roles_list)) & (UserRole.user_id == self.id)
            ).gino.status()
            user = await self.get(self.id)
            assigned_roles = await user.roles
            await system_logger.debug(
                _local_("User {} roles: {}.").format(user.username, assigned_roles)
            )
            return remove

    # permissions
    async def get_permissions_from_groups(self):
        """Возвращает список разрешений полученных от групп, в которых пользователь состоит."""
        user_groups = await self.assigned_groups

        permissions_from_group = list()
        # если захотеть можно сделать одним запросом к бд
        for group in user_groups:
            permissions_list = await group.get_permissions()
            permissions_from_group += permissions_list
        return permissions_from_group

    async def get_permissions(self):
        is_superuser = await self.superuser()
        if is_superuser:
            all_permissions_set = set(TkPermission)
            return all_permissions_set

        # personal permissions
        user_permissions = (
            await UserTkPermission.query.order_by(UserTkPermission.permission)
            .where(UserTkPermission.user_id == self.id)
            .gino.all()
        )
        all_permissions_list = [
            permission.permission for permission in user_permissions
        ]
        # permissions from group
        permissions_from_group = await self.get_permissions_from_groups()
        all_permissions_list += permissions_from_group

        permissions_set = set(all_permissions_list)
        return permissions_set

    async def add_permissions(self, permissions_list, creator):

        async with db.transaction():
            for permission in permissions_list:
                try:
                    await UserTkPermission.create(
                        user_id=self.id, permission=permission
                    )
                except UniqueViolationError:  # пара user_id и permission уникальна
                    raise SimpleError(
                        _local_("User {} already has permission {}.").format(
                            self.id, permission
                        ),
                        user=creator,
                    )

        permissions_str = ", ".join(permissions_list)
        await system_logger.info(
            _local_("Permission(s) {} added to user {}.").format(
                permissions_str, self.username
            ),
            user=creator,
            entity=self.entity,
        )

    async def remove_permissions(self, permissions_list=None, creator="system"):
        if not permissions_list:
            return await UserTkPermission.delete.where(
                UserTkPermission.user_id == self.id
            ).gino.status()

        if permissions_list and isinstance(permissions_list, list):

            remove = await UserTkPermission.delete.where(
                (UserTkPermission.permission.in_(permissions_list))
                & (UserTkPermission.user_id == self.id)  # noqa: W503
            ).gino.status()

            # log
            permissions_str = ", ".join(permissions_list)
            await system_logger.info(
                _local_("Permission(s) {} removed from user {}.").format(
                    permissions_str, self.username
                ),
                user=creator,
                entity=self.entity,
            )

            assigned_permissions = await self.get_permissions()
            await system_logger.debug(
                _local_("User {} permission(s): {}.").format(
                    self.username, assigned_permissions
                )
            )

            return remove

    async def activate(self, creator):
        query = User.update.values(is_active=True).where(User.id == self.id)
        operation_status = await query.gino.status()

        if PAM_AUTH and not self.by_ad:
            return await self.pam_unlock(creator=creator)

        info_message = _local_("User {username} has been activated.").format(
            username=self.username
        )
        await system_logger.info(info_message, entity=self.entity, user=creator)
        return operation_status

    async def pam_unlock(self, creator):
        """Разблокировать пользователя в ОС."""
        result = await veil_auth_class.user_unlock(username=self.username)
        if result.success:
            info_message = _local_(
                "User {username} has been activated on Astra.").format(
                username=self.username
            )
            await system_logger.info(info_message, entity=self.entity, user=creator)
        else:
            warning_message = result.error_msg
            await system_logger.warning(
                warning_message, entity=self.entity, user=creator
            )
        return result.success

    async def deactivate(self, creator):
        """Деактивировать всех суперпользователей в системе - нельзя."""
        query = db.select([db.func.count(User.id)]).where(
            (User.id != self.id)
            & (User.is_superuser == True)  # noqa: W503, E712
            & (User.is_active == True)  # noqa: W503, E712
        )

        superuser_count = await query.gino.scalar()
        if superuser_count == 0:
            raise SimpleError(_local_("There is no more active superuser."),
                              user=creator)

        query = User.update.values(is_active=False).where(User.id == self.id)
        operation_status = await query.gino.status()

        if PAM_AUTH and not self.by_ad:
            return await self.pam_lock(creator=creator)

        info_message = _local_("User {username} has been deactivated.").format(
            username=self.username
        )
        await system_logger.info(info_message, entity=self.entity, user=creator)

        # Удаляем ранее выданный токен
        await UserJwtInfo.delete.where(UserJwtInfo.user_id == self.id).gino.status()

        # Разорвать соединение ТК, если присутствуют
        cmd_dict = dict(command=ThinClientCmd.DISCONNECT.name, user_id=str(self.id))
        await publish_to_redis(REDIS_THIN_CLIENT_CMD_CHANNEL, json.dumps(cmd_dict))

        # Удаляем владения ВМ пользователем
        await EntityOwner.delete.where(EntityOwner.user_id == self.id).gino.status()

        return operation_status

    async def pam_lock(self, creator):
        """Заблокировать пользователя в ОС."""
        result = await veil_auth_class.user_lock(username=self.username)
        if result.success:
            info_message = _local_(
                "User {username} has been deactivated on Astra.").format(
                username=self.username
            )
            await system_logger.info(info_message, entity=self.entity, user=creator)
        else:
            warning_message = result.error_msg
            await system_logger.warning(
                warning_message, entity=self.entity, user=creator
            )
        return result.success

    @staticmethod
    async def check_email(email):
        email_count = (
            await db.select([db.func.count()]).where(User.email == email).gino.scalar()
        )
        return email_count < 1

    @staticmethod
    async def check_user(username, raw_password):
        count = (
            await db.select([db.func.count()])
            .where((User.username == username) & (User.is_active == True))  # noqa: E712
            .gino.scalar()
        )
        if count == 0:
            return False
        if PAM_AUTH:
            return await User.pam_check_user(username, raw_password)
        return await User.check_password(username, raw_password)

    @staticmethod
    async def check_password(username, raw_password):
        password = (
            await User.select("password").where(User.username == username).gino.scalar()
        )
        return await hashers.check_password(raw_password, password)

    @staticmethod
    async def pam_check_user(username: str, password: str) -> VeilAuthResult:
        """Call linux auth via veil-aio-au."""
        result = await veil_auth_class.user_authenticate(
            username=username, password=password
        )
        if not result.success:
            raise MeaningError(_local_("Invalid credentials. Check or create password for user {}.").format(username))
        return result.success

    async def pam_set_password(self, raw_password: str, creator):
        """Задает пароль пользователя в ОС."""
        result = await veil_auth_class.user_set_password(
            username=self.username, new_password=raw_password
        )
        if result.success:
            info_message = _local_(
                "Password of user {username} has been changed.").format(
                username=self.username
            )
            await system_logger.info(info_message, entity=self.entity, user=creator)
        else:
            error_message = _local_(
                "Password of user {username} has`t been changed.").format(
                username=self.username
            )
            await system_logger.error(error_message, entity=self.entity, user=creator)
        return result.success

    async def pam_user_in_group(self, group: str) -> bool:
        result = await veil_auth_class.user_in_group(self.username, group)
        return result

    async def pam_user_add_group(self, group: str) -> VeilAuthResult:
        return await veil_auth_class.user_add_group(username=self.username, group=group)

    async def pam_user_remove_group(self, group: str) -> VeilAuthResult:
        return await veil_auth_class.user_remove_group(
            username=self.username, group=group
        )

    async def pam_user_set_email(self, email: str) -> VeilAuthResult:
        gecos = ",VDI,,,{}".format(email)
        return await veil_auth_class.user_set_gecos(username=self.username, gecos=gecos)

    async def set_password(self, raw_password, creator):
        # Save old password in history
        await PasswordHistory.soft_create(user_id=self.id)

        # Set password expiration date
        expiration_date = await self.get_password_expiration_date()
        await User.update.values(
            password_expiration_date=expiration_date
        ).where(User.id == self.id).gino.status()

        if PAM_AUTH and not self.by_ad:
            pam_result = await self.pam_create_user(raw_password=raw_password)
            if pam_result.success:
                return pam_result.success
            return await self.pam_set_password(
                raw_password=raw_password, creator=creator
            )

        encoded_password = hashers.make_password(raw_password, salt=SECRET_KEY)
        user_status = (
            await User.update.values(password=encoded_password)
            .where(User.id == self.id)
            .gino.status()
        )
        if not self.local_password:
            await self.update(local_password=True).apply()
            info_message = _local_("Password of user {} has been changed to the local password.").format(self.username)
            await system_logger.warning(info_message, entity=self.entity, user=creator)
        else:
            info_message = _local_("Password of user {username} has been changed.").format(
                username=self.username
            )
            await system_logger.info(info_message, entity=self.entity, user=creator)

        # Удаляем ранее выданный токен
        await UserJwtInfo.delete.where(UserJwtInfo.user_id == self.id).gino.status()

        return user_status

    @staticmethod
    async def get_password_expiration_date():
        expiration_date = None
        expiration_period = await Settings.get_settings("PASSWORD_EXPIRATION_PERIOD")

        if expiration_period and expiration_period != 0:
            today = datetime.datetime.now(datetime.timezone.utc)
            timedelta = datetime.timedelta(days=abs(expiration_period))
            expiration_date = today + timedelta
            await system_logger.debug(
                _local_("Password expires {}.").format(expiration_date.date())
            )
        return expiration_date

    @staticmethod
    async def check_password_expiration(username):
        expiration_date = (
            await User.select("password_expiration_date").where(User.username == username).gino.scalar()
        )
        is_expired = False
        if expiration_date:
            today = datetime.datetime.now(datetime.timezone.utc)
            is_expired = today > expiration_date
        return is_expired

    async def pam_create_user(
        self, raw_password: str, superuser: bool = False
    ) -> VeilAuthResult:
        """Create new user in the OS.

        GECOS: https://en.wikipedia.org/wiki/Gecos_field
        """
        gecos = ",VDI,,,{}".format(self.email) if self.email else ",VDI,,,"
        if raw_password:
            result = await veil_auth_class.user_create_new(
                username=self.username,
                password=raw_password,
                gecos=gecos,
                group=PAM_USER_GROUP,
            )
        else:
            result = await veil_auth_class.user_create(
                username=self.username, group=PAM_USER_GROUP, gecos=gecos
            )
        if result.success and superuser:
            pam_result = await self.pam_user_add_group(PAM_SUPERUSER_GROUP)
            if not pam_result.success:
                return pam_result
        return result

    async def convert_to_ad_user(self, username, first_name, last_name, email, creator):
        """Convert local user to ad user."""
        if self.by_ad:
            return

        encoded_password = hashers.make_password(None, salt=SECRET_KEY)  # to remove local password
        await self.update(password=encoded_password,
                          first_name=first_name,
                          last_name=last_name,
                          email=email,
                          is_superuser=False,
                          is_active=True,
                          by_ad=True,
                          local_password=False).apply()

        entity = {"entity_type": EntityType.AUTH, "entity_uuid": None}
        await system_logger.info(
            _local_(f"Local user {username} was converted to domain user."),
            entity=entity, user=creator)

    @classmethod
    async def soft_create(
        cls,
        username,
        creator,
        password=None,
        email=None,
        last_name=None,
        first_name=None,
        is_superuser=False,
        id=None,
        groups=None,
        is_active=True,
        two_factor=False,
        secret=None,
        by_ad=False,
        local_password=True,
        logging=True
    ):
        """Если password будет None, то make_password вернет unusable password."""
        if by_ad:
            if not username:
                raise SimpleError(_local_("username can`t be empty."))
        else:
            username = await cls.validate_username(username)
        encoded_password = hashers.make_password(password, salt=SECRET_KEY)
        user_kwargs = {
            "username": username,
            "password": encoded_password,
            "is_active": is_active,
            "is_superuser": is_superuser,
            "two_factor": two_factor,
            "secret": secret,
            "by_ad": by_ad,
            "local_password": local_password
        }
        if email:
            user_kwargs["email"] = email
        if last_name:
            user_kwargs["last_name"] = last_name
        if first_name:
            user_kwargs["first_name"] = first_name
        if id:
            user_kwargs["id"] = id
        password_expiration_date = await cls.get_password_expiration_date()
        if password_expiration_date:
            user_kwargs["password_expiration_date"] = password_expiration_date

        user_role = _local_("Superuser.") if is_superuser else _local_("User.")

        user_obj = None
        try:
            user_obj = await cls.create(**user_kwargs)
            if PAM_AUTH and not user_obj.by_ad:
                pam_result = await user_obj.pam_create_user(
                    raw_password=password, superuser=is_superuser
                )
                if not pam_result.success:
                    # TODO: Добавить pam удаление пользователя на астре
                    # pam_result.return_code == 969 - ошибка пароля на астре
                    if pam_result.return_code == 969:
                        # деактивируем пользователя и сообщаем об ошибке пароля
                        await user_obj.deactivate(creator)
                        user_role = _local_("User.")
                        msg = _local_(
                            "You must change password for user {}. Check a reason in description.".format(
                                username))
                        await system_logger.warning(
                            message=msg,
                            entity=user_obj.entity,
                            user=creator,
                            description=str(pam_result),
                        )
                    elif (pam_result.return_code == 1) and ("adduser" in pam_result.error_msg):
                        checked = await User.pam_check_user(username, password)
                        user_role = _local_("User.")
                        if not checked:
                            await user_obj.delete()
                            raise SilentError(_local_(
                                "User {} was created in Astra Linux before. Please try to create him with correct password or delete in Astra Linux before trying to create in VeiL VDI again.").format(
                                username))
                    else:
                        msg = _local_(
                            "User {} was created in Astra Linux before. Please delete him there before trying to create in Broker again.").format(
                            username)
                        await system_logger.warning(
                            message=msg,
                            entity=user_obj.entity,
                            user=creator,
                        )
                        await user_obj.delete()
                        raise PamError(pam_result)
        except (PamError, UniqueViolationError) as err_msg:
            msg = _local_("User {} creation error.").format(username)
            await system_logger.error(
                message=msg,
                entity={"entity_type": EntityType.USER, "entity_uuid": None},
                user=creator,
                description=str(err_msg),
            )
            if user_obj:
                await user_obj.delete()
            raise AssertionError(msg)
        except SilentError as err_msg:
            msg = _local_("Your password is incorrect for user {}. Check description in journal.".format(
                username))
            await system_logger.error(
                message=msg,
                entity={"entity_type": EntityType.USER, "entity_uuid": None},
                user=creator,
                description=str(err_msg),
            )
            raise AssertionError(msg)

        if logging:
            info_message = _local_("{} {} created.").format(user_role[:-1], username)
            await system_logger.info(info_message, entity=user_obj.entity, user=creator)

        if groups:
            for group in groups:
                group = await Group.get(group.id)
                await group.add_user(user_id=user_obj.id, creator=creator)

        # По дефолту пользователь получает все права на работу с тк
        for permission in TkPermission:
            await UserTkPermission.create(
                user_id=user_obj.id, permission=permission.value
            )

        return user_obj

    @classmethod
    async def soft_update(
        cls,
        id,
        creator: str,
        email: str = None,
        last_name: str = None,
        first_name: str = None,
        is_superuser: str = None,
        two_factor: bool = None
    ):
        try:
            async with db.transaction():
                update_type, update_dict = await super().soft_update(
                    id,
                    email=email,
                    last_name=last_name,
                    first_name=first_name,
                    is_superuser=is_superuser,
                    two_factor=two_factor,
                    creator=creator,
                )
                user_obj = await User.get(id)
                if PAM_AUTH and not user_obj.by_ad:
                    # Параметры с фронта приходят по 1му, поэтому не страшно
                    if update_dict.get("is_superuser") is False:
                        pam_result = await update_type.pam_user_remove_group(
                            PAM_SUPERUSER_GROUP
                        )
                    elif "is_superuser" in update_dict and update_dict.get(
                        "is_superuser"
                    ):
                        pam_result = await update_type.pam_user_add_group(
                            PAM_SUPERUSER_GROUP
                        )
                    elif "email" in update_dict and update_dict.get("email"):
                        pam_result = await update_type.pam_user_set_email(email=email)
                    else:
                        pam_result = None
                    if pam_result and not pam_result.success:
                        raise PamError(pam_result)

        except PamError as err_msg:
            msg = _local_("User {} update error.").format(update_type.username)
            await system_logger.error(
                message=msg,
                entity={"entity_type": EntityType.USER, "entity_uuid": id},
                user=creator,
                description=err_msg,
            )
            raise AssertionError(msg)

        creator = update_dict.pop("creator")
        desc = str(update_dict)
        await system_logger.info(
            _local_("Values of user {} is changed.").format(update_type.username),
            description=desc,
            user=creator,
            entity=update_type.entity,
        )

        if "is_superuser" in update_dict and update_dict.get("is_superuser"):
            assigned_roles = _local_("Roles: {}.".format(str(await update_type.roles)))
            info_message = _local_("User {username} has become a superuser.").format(
                username=update_type.username
            )
            await system_logger.info(
                info_message,
                entity=update_type.entity,
                description=assigned_roles,
                user=creator,
            )
        elif update_dict.get("is_superuser") is False:
            assigned_roles = _local_("Roles: {}.".format(str(await update_type.roles)))
            info_message = _local_("User {username} is no longer a superuser.").format(
                username=update_type.username
            )
            await system_logger.info(
                info_message,
                entity=update_type.entity,
                description=assigned_roles,
                user=creator,
            )

        return update_type

    @classmethod
    async def login(cls, username, token, client_type, ip=None, ldap=False):
        """Записывает данные с которыми пользователь вошел в систему."""
        user = await User.get_object(
            extra_field_name="username", extra_field_value=username
        )
        if not user:
            return False

        await user.update(last_login=func.now()).apply()

        # Удаляем ранее выданный токен
        await UserJwtInfo.delete.where(UserJwtInfo.user_id == user.id).gino.status()

        # Записываем новый токен
        await UserJwtInfo.soft_create(user_id=user.id, token=token)

        # Login event
        auth_type = "Ldap" if ldap else "Local"
        info_message = _local_("User {username} has been logged in.").format(
            username=username
        )
        description = _local_("Auth type: {}, IP: {}, Client type: {}.").format(
            auth_type, ip,
            client_type)
        await system_logger.info(
            info_message, entity=user.entity, description=description
        )
        return True

    @classmethod
    async def logout(cls, username, access_token):
        user = await User.get_object(
            extra_field_name="username", extra_field_value=username
        )
        if not user:
            return False
        # Проверяем, что нет попытки прервать запрещенный ранее токен
        is_valid = await UserJwtInfo.check_token(username, access_token)
        if not is_valid:
            return False

        # Запрещаем все выданные пользователю токены (Может быть только 1)
        await UserJwtInfo.delete.where(UserJwtInfo.user_id == user.id).gino.status()

        info_message = _local_("User {username} has been logged out.").format(
            username=username
        )
        await system_logger.info(info_message, entity=user.entity)
        return True

    async def generate_qr(self, creator="system", repeat=False):
        if repeat:
            secret_set = await User.select("secret").where(User.username == self.username).gino.first()
            secret = secret_set[0]
        else:
            secret = pyotp.random_base32()
            await self.update(secret=secret).apply()
        qr_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=self.username, issuer_name="VeiL VDI")

        if repeat:
            await system_logger.info(
                _local_("QR code and secret code of 2fa were repeated for user {}.").format(self.username),
                user=creator, entity=self.entity)
        else:
            await system_logger.info(
                _local_("New QR code and secret code of 2fa were generated for user {}.").format(self.username),
                user=creator, entity=self.entity)
        return {"qr_uri": qr_uri, "secret": secret}

    @staticmethod
    async def check_2fa(username, code):
        try:
            two_factor = await User.select("two_factor").where(User.username == username).gino.first()
            if two_factor:
                if two_factor[0]:
                    if isinstance(code, str):
                        secret = await User.select("secret").where(User.username == username).gino.first()
                        totp = pyotp.TOTP(secret[0])
                        if totp.now() == code:
                            return True
                    raise SilentError(_local_("One-time password does not match or is out of date."))
        except AssertionError as e:
            raise AssertionError(e)
        return False


class UserJwtInfo(db.Model):
    """При авторизации пользователя выполняется запись.

    В поле last_changed хранится дата последнего изменения токена. При изменении пароля/логауте/перегенерации токена
    значение поля меняется, вследствие чего токены, сгенерированные с помощью старых значений
    становятся невалидными.
    """

    __tablename__ = "user_jwtinfo"

    user_id = db.Column(
        UUID(), db.ForeignKey(User.id, ondelete="CASCADE"), primary_key=True
    )
    # не хранит в себе 'jwt ' максимальный размер намеренно не установлен, т.к. четкого ограничение в стандарте нет.
    token = db.Column(db.Unicode(), nullable=False, index=True)
    last_changed = db.Column(db.DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def soft_create(cls, user_id, token):
        # Не нашел в GINO create_or_update.

        count = (
            await db.select([db.func.count()])
            .where(UserJwtInfo.user_id == user_id)
            .gino.scalar()
        )
        if count == 0:
            # Если записи для пользователя нет - создаем новую.
            await UserJwtInfo.create(user_id=user_id, token=token)
            return True
        # Если запись уже существует - обновлям значение токена.
        await UserJwtInfo.update.values(token=token, last_changed=func.now()).where(
            UserJwtInfo.user_id == user_id
        ).gino.status()
        return True

    @classmethod
    async def check_token(cls, username, token):
        """Проверяет соответствие выданного токена тому, что пришел в payload."""
        user_obj = await User.get_object(
            extra_field_name="username", extra_field_value=username
        )
        if not user_obj:
            return False
        count = (
            await db.select([db.func.count()])
            .where((UserJwtInfo.user_id == user_obj.id) & (UserJwtInfo.token == token))
            .gino.scalar()
        )
        return count > 0


class Group(AbstractSortableStatusModel, VeilModel):
    __tablename__ = "group"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    description = db.Column(db.Unicode(length=255), nullable=True, unique=False)
    date_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    # На тестовых серверах были проблемы с форматом в AuthenticationDirectory.
    ad_guid = db.Column(db.Unicode(length=36), nullable=True, unique=True)
    ad_cn = db.Column(db.Unicode(length=1000), nullable=True, unique=True)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    def entity_type(self):
        return EntityType.GROUP

    @property
    async def roles(self):
        query = GroupRole.select("role").where(GroupRole.group_id == self.id)
        return await query.gino.all()

    @property
    def possible_users_query(self):
        possible_users_query = (
            User.join(
                UserGroup.query.where(UserGroup.group_id == self.id).alias("query_1"),
                isouter=True,
            ).select().where((text("query_1.id is null")) & (User.is_active))
        )
        return possible_users_query

    async def possible_users(self, limit=100, offset=0, username=""):
        """Берем всех АКТИВНЫХ пользователей и исключаем тех, кому уже назначена группа."""
        return (
            await self.possible_users_query.where(User.username.ilike("%{}%".format(username))).order_by(
                User.username).limit(limit).offset(offset).gino.load(User).all()
        )

    @property
    def assigned_users_query(self):
        return User.join(
            UserGroup.query.where(UserGroup.group_id == self.id).alias()
        ).select()

    @property
    async def assigned_users(self):
        return await self.assigned_users_query.gino.load(User).all()

    async def assigned_users_paginator(self, limit, offset, username=""):
        return (
            await self.assigned_users_query.limit(limit)
            .where(User.username.ilike("%{}%".format(username)))
            .offset(offset)
            .gino.load(User)
            .all()
        )

    @staticmethod
    async def soft_create(
        verbose_name, creator, description=None, id=None, ad_guid=None, ad_cn=None
    ):
        group_kwargs = {"verbose_name": verbose_name, "description": description}
        if ad_guid:
            group_kwargs["ad_guid"] = str(ad_guid)
        if id:
            group_kwargs["id"] = id
        if ad_cn:
            group_kwargs["ad_cn"] = ad_cn
        group_obj = await Group.create(**group_kwargs)
        info_message = _local_("Group {} is created.").format(verbose_name)
        await system_logger.info(info_message, user=creator, entity=group_obj.entity)

        return group_obj

    @staticmethod
    async def user_belongs_to_group(user_id, group_id):
        """Check uf user belongs to group."""
        rel = await UserGroup.query.where(
            (UserGroup.user_id == user_id) & (UserGroup.group_id == group_id)).gino.first()
        return bool(rel is not None)

    # permissions
    async def get_permissions(self):
        query = (
            GroupTkPermission.select("permission")
            .order_by(GroupTkPermission.permission)
            .where(GroupTkPermission.group_id == self.id)
        )
        query_res = await query.gino.all()
        # print('query_res: ', query_res, flush=True)
        permissions_list = [permission.permission for permission in query_res]
        return permissions_list

    async def add_permissions(self, permissions_list, creator):

        async with db.transaction():
            for permission in permissions_list:
                try:
                    await GroupTkPermission.create(
                        group_id=self.id, permission=permission
                    )
                except UniqueViolationError:  # пара group_id и permission уникальна
                    raise SimpleError(
                        _local_("Group {} already has permission {}.").format(
                            self.id, permission
                        ),
                        user=creator,
                    )

        permissions_str = ", ".join(permissions_list)
        await system_logger.info(
            _local_("Permission(s) {} added to group {}.").format(
                permissions_str, self.verbose_name
            ),
            user=creator,
            entity=self.entity,
        )

    async def remove_permissions(self, permissions_list=None, creator="system"):
        if not permissions_list:
            return await GroupTkPermission.delete.where(
                GroupTkPermission.group_id == self.id
            ).gino.status()

        if permissions_list and isinstance(permissions_list, list):

            remove = await GroupTkPermission.delete.where(
                (GroupTkPermission.permission.in_(permissions_list))
                & (GroupTkPermission.group_id == self.id)  # noqa: W503
            ).gino.status()

            # log
            permissions_str = ", ".join(permissions_list)
            await system_logger.info(
                _local_("Permission(s) {} removed from group {}.").format(
                    permissions_str, self.verbose_name
                ),
                user=creator,
                entity=self.entity,
            )

            assigned_permissions = await self.get_permissions()
            await system_logger.debug(
                _local_("Group {} permission(s): {}.").format(
                    self.verbose_name, assigned_permissions
                )
            )

            return remove

    async def soft_update(self, verbose_name, description, creator):
        group_kwargs = dict()
        if verbose_name:
            group_kwargs["verbose_name"] = verbose_name
        if description:
            group_kwargs["description"] = description

        if group_kwargs:
            await self.update(**group_kwargs).apply()
            desc = str(group_kwargs)
            await system_logger.info(
                _local_("Values of group {} is updated.").format(self.verbose_name),
                description=desc,
                user=creator,
                entity=self.entity,
            )

        return self

    async def add_user(self, user_id, creator, logging=True):
        """Add user to group."""
        try:
            user_in_group = await db.scalar(
                db.exists(
                    UserGroup.query.where(UserGroup.user_id == user_id).where(
                        UserGroup.group_id == self.id
                    )
                ).select()
            )
            if user_in_group:
                return
            user_group = await UserGroup.create(user_id=user_id, group_id=self.id)
            if logging:
                user = await User.get(user_id)
                info_message = _local_("User {} has been included to group {}.").format(
                    user.username, self.verbose_name
                )
                await system_logger.info(info_message, entity=self.entity, user=creator)
            return user_group
        except UniqueViolationError:
            raise SimpleError(
                _local_("User {} is already in group {}.").format(user_id, self.id)
            )

    async def add_users(self, user_id_list, creator, logging=True):
        async with db.transaction():
            for user in user_id_list:
                await self.add_user(user, creator, logging)

    async def remove_users(self, creator: str, user_id_list: list):
        for id in user_id_list:
            name = await User.get(id)
            await system_logger.info(
                _local_("Removing user {} from group {}.").format(
                    name.username, self.verbose_name
                ),
                user=creator,
                entity=self.entity,
            )
        return await UserGroup.delete.where(
            (UserGroup.user_id.in_(user_id_list)) & (UserGroup.group_id == self.id)
        ).gino.status()

    async def add_role(self, role, creator):
        try:
            group_role = await GroupRole.create(group_id=self.id, role=role)
            info_message = _local_("Role {} has been set to group {}.").format(
                role, self.verbose_name
            )
            await system_logger.info(info_message, entity=self.entity, user=creator)

        except UniqueViolationError:
            raise SimpleError(
                _local_("Group {} has already role {}.").format(self.id, role),
                user=creator
            )
        return group_role

    async def add_roles(self, roles_list, creator):
        async with db.transaction():
            for role in roles_list:
                await self.add_role(role, creator)

    async def remove_roles(self, roles_list, creator):
        role_del = " ".join(roles_list)
        await system_logger.info(
            _local_("Roles: {} was deleted to group {}.").format(role_del,
                                                                 self.verbose_name),
            user=creator,
            entity=self.entity,
        )
        return await GroupRole.delete.where(
            (GroupRole.role.in_(roles_list)) & (GroupRole.group_id == self.id)
        ).gino.status()


class UserGroup(db.Model):
    __tablename__ = "user_groups"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        UUID(), db.ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    group_id = db.Column(
        UUID(), db.ForeignKey(Group.id, ondelete="CASCADE"), nullable=False
    )


class GroupRole(db.Model):
    __tablename__ = "group_role"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    role = db.Column(AlchemyEnum(Role), nullable=False, index=True)
    group_id = db.Column(
        UUID(), db.ForeignKey(Group.id, ondelete="CASCADE"), nullable=False
    )


class UserRole(db.Model):
    __tablename__ = "user_role"
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    role = db.Column(AlchemyEnum(Role), nullable=False, index=True)
    user_id = db.Column(
        UUID(), db.ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )


class PasswordHistory(db.Model):
    __tablename__ = "password_history"
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        UUID(), db.ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    password = db.Column(db.Unicode(length=128), nullable=False)
    changed = db.Column(db.DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def soft_create(cls, user_id):
        password = await User.select("password").where(User.id == user_id).gino.first()
        kwargs = {
            "user_id": user_id,
            "password": password[0]
        }
        model = await cls.create(**kwargs)
        return model

    @classmethod
    async def get_encoded_passwords(cls, user_id):
        encoded_passwords = await cls.select("password").where(
            cls.user_id == user_id).gino.all()

        if encoded_passwords:
            encoded_passwords_list = [
                password[0] for password in encoded_passwords
            ]
            return encoded_passwords_list
        return

    @classmethod
    async def check_history_match(cls, user_id, raw_password):
        current_password = await User.select("password").where(User.id == user_id).gino.first()
        current_password = current_password[0]
        encoded_password = hashers.make_password(raw_password, salt=SECRET_KEY)
        history = await cls.get_encoded_passwords(user_id)
        if (current_password == encoded_password) or (history and encoded_password in history):
            return True
        else:
            return False


# -------- Составные индексы --------------------------------
Index(
    "ix_entity_entity_object_entity_type",
    Entity.entity_uuid,
    Entity.entity_type,
    unique=True,
)

Index("ix_user_in_group", UserGroup.user_id, UserGroup.group_id, unique=True)
Index("ix_user_roles_user_roles", UserRole.role, UserRole.user_id, unique=True)
Index("ix_group_roles_group_roles", GroupRole.role, GroupRole.group_id, unique=True)

Index(
    "ix_entity_owner_entity_user",
    EntityOwner.entity_id,
    EntityOwner.user_id,
    unique=True,
)
Index(
    "ix_entity_owner_entity_group",
    EntityOwner.entity_id,
    EntityOwner.group_id,
    unique=True,
)
Index(
    "ix_entity_owner_entity_owner",
    EntityOwner.entity_id,
    EntityOwner.group_id,
    EntityOwner.user_id,
    unique=True,
)
