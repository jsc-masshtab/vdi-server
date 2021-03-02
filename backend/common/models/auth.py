# -*- coding: utf-8 -*-
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy import Index
from sqlalchemy import Enum as AlchemyEnum
from asyncpg.exceptions import UniqueViolationError
from veil_aio_au import VeilResult as VeilAuthResult

from common.settings import PAM_AUTH, PAM_USER_GROUP, PAM_SUPERUSER_GROUP, SECRET_KEY
from common.database import db
from common.veil.veil_gino import (
    AbstractSortableStatusModel,
    Role,
    EntityType,
    VeilModel,
)
from common.veil.veil_errors import SimpleError, PamError
from common.veil.auth import hashers
from common.languages import lang_init
from common.log.journal import system_logger
from common.veil.auth.veil_pam import veil_auth_class


from common.models.user_tk_permission import (
    TkPermission,
    UserTkPermission,
    GroupTkPermission,
)

_ = lang_init()


class Entity(db.Model):
    """
    entity_type: тип сущности из Enum
    entity_uuid: UUID сущности, если в качестве EntityType указано название таблицы
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
       Если role пустой, то только по пользователю"""

    __tablename__ = "entity_owner"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(), db.ForeignKey(Entity.id, ondelete="CASCADE"))
    user_id = db.Column(
        UUID(), db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )
    group_id = db.Column(
        UUID(), db.ForeignKey("group.id", ondelete="CASCADE"), nullable=True
    )


class User(AbstractSortableStatusModel, VeilModel):
    __tablename__ = "user"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
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

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    def entity_type(self):
        return EntityType.USER

    async def superuser(self) -> bool:
        """Should be used instead of is_superuser attr."""
        if PAM_AUTH:
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

    @property
    async def pools(self):
        # Либо размещать staticmethod в пулах, либо импорт тут, либо хардкодить названия полей.
        from common.models.pool import Pool

        is_superuser = await self.superuser()
        if is_superuser:
            # superuser есть все роли - мы просто выбираем все доступные пулы.
            pools_query = Pool.get_pools_query()
        else:
            user_roles = await self.roles
            user_groups_ids = await self.assigned_groups_ids
            pools_query = Pool.get_pools_query(
                user_id=self.id, groups_ids_list=user_groups_ids, role_set=user_roles
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
            }
            for pool in pools
        ]

        return pools_list

    @staticmethod
    async def get_id(username):
        return await User.select("id").where(User.username == username).gino.scalar()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    async def add_role(self, role, creator):
        try:
            await system_logger.info(
                _("Role {} is added to user {}.").format(role, self.username),
                user=creator,
                entity=self.entity,
            )
            add = await UserRole.create(user_id=self.id, role=role)
            user = await self.get(self.id)
            assigned_roles = await user.roles
            await system_logger.debug(
                _("User {} roles: {}.").format(user.username, assigned_roles)
            )
            return add
        except UniqueViolationError:
            raise SimpleError(
                _("Role {} is assigned to user {}.").format(role, self.id), user=creator
            )

    async def remove_roles(self, roles_list=None, creator="system"):
        if not roles_list:
            return await UserRole.delete.where(
                UserRole.user_id == self.id
            ).gino.status()
        if roles_list and isinstance(roles_list, list):
            role_del = " ".join(roles_list)
            await system_logger.info(
                _("Roles: {} was deleted to user {}.").format(role_del, self.username),
                user=creator,
                entity=self.entity,
            )
            remove = await UserRole.delete.where(
                (UserRole.role.in_(roles_list)) & (UserRole.user_id == self.id)
            ).gino.status()
            user = await self.get(self.id)
            assigned_roles = await user.roles
            await system_logger.debug(
                _("User {} roles: {}.").format(user.username, assigned_roles)
            )
            return remove

    # permissions
    async def get_permissions_from_groups(self):
        """Возвращает список разрешений полученных от групп, в которых пользователь состоит"""
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
                        _("User {} already has permission {}.").format(
                            self.id, permission
                        ),
                        user=creator,
                    )

        permissions_str = ", ".join(permissions_list)
        await system_logger.info(
            _("Permission(s) {} added to user {}.").format(
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
                _("Permission(s) {} removed from user {}.").format(
                    permissions_str, self.username
                ),
                user=creator,
                entity=self.entity,
            )

            assigned_permissions = await self.get_permissions()
            await system_logger.debug(
                _("User {} permission(s): {}.").format(
                    self.username, assigned_permissions
                )
            )

            return remove

    async def remove_groups(self, creator="system"):
        groups = await self.assigned_groups
        users_list = [self.id]
        for group in groups:
            await group.remove_users(creator=creator, user_id_list=users_list)
            await system_logger.info(
                _("Group {} is removed for user {}.").format(group, self.username),
                entity=self.entity,
            )

    async def activate(self, creator):
        query = User.update.values(is_active=True).where(User.id == self.id)
        operation_status = await query.gino.status()

        info_message = _("User {username} has been activated.").format(
            username=self.username
        )
        await system_logger.info(info_message, entity=self.entity, user=creator)

        if PAM_AUTH:
            return await self.pam_unlock(creator=creator)
        return operation_status

    async def pam_unlock(self, creator):
        """Разблокировать пользователя в ОС."""
        result = await veil_auth_class.user_unlock(username=self.username)
        if result.success:
            info_message = _("User {username} has been activated on Astra.").format(
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
            raise SimpleError(_("There is no more active superuser."), user=creator)

        query = User.update.values(is_active=False).where(User.id == self.id)
        operation_status = await query.gino.status()

        info_message = _("User {username} has been deactivated.").format(
            username=self.username
        )
        await system_logger.info(info_message, entity=self.entity, user=creator)

        if PAM_AUTH:
            return await self.pam_lock(creator=creator)
        return operation_status

    async def pam_lock(self, creator):
        """Заблокировать пользователя в ОС."""
        result = await veil_auth_class.user_lock(username=self.username)
        if result.success:
            info_message = _("User {username} has been deactivated on Astra.").format(
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
        return result.success

    async def pam_set_password(self, raw_password: str, creator):
        """Задает пароль пользователя в ОС."""
        result = await veil_auth_class.user_set_password(
            username=self.username, new_password=raw_password
        )
        if result.success:
            info_message = _("Password of user {username} has been changed.").format(
                username=self.username
            )
            await system_logger.info(info_message, entity=self.entity, user=creator)
        else:
            error_message = _("Password of user {username} has`t been changed.").format(
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
        if PAM_AUTH:
            return await self.pam_set_password(
                raw_password=raw_password, creator=creator
            )

        encoded_password = hashers.make_password(raw_password, salt=SECRET_KEY)
        user_status = (
            await User.update.values(password=encoded_password)
            .where(User.id == self.id)
            .gino.status()
        )

        info_message = _("Password of user {username} has been changed.").format(
            username=self.username
        )
        await system_logger.info(info_message, entity=self.entity, user=creator)

        return user_status

    async def pam_create_user(
        self, raw_password: str, superuser: bool = False
    ) -> VeilAuthResult:
        """Create new user in the OS.

        GECOS: https://en.wikipedia.org/wiki/Gecos_field
        """
        # full_name = ' '.join([self.last_name, self.first_name])
        # gecos = '"{}",VDI,,,{}'.format(full_name, self.email)  # type: str
        gecos = ",VDI,,,{}".format(self.email)  # type: str
        result = await veil_auth_class.user_create_new(
            username=self.username,
            password=raw_password,
            gecos=gecos,
            group=PAM_USER_GROUP,
        )
        if result.success and superuser:
            pam_result = await self.pam_user_add_group(PAM_SUPERUSER_GROUP)
            if not pam_result.success:
                return pam_result
        return result

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
        is_active=True,
    ):
        """Если password будет None, то make_password вернет unusable password"""
        encoded_password = hashers.make_password(password, salt=SECRET_KEY)
        user_kwargs = {
            "username": username,
            "password": encoded_password,
            "is_active": is_active,
            "is_superuser": is_superuser,
        }
        if email:
            user_kwargs["email"] = email
        if last_name:
            user_kwargs["last_name"] = last_name
        if first_name:
            user_kwargs["first_name"] = first_name
        if id:
            user_kwargs["id"] = id

        try:
            async with db.transaction():
                user_obj = await cls.create(**user_kwargs)
                if PAM_AUTH:
                    pam_result = await user_obj.pam_create_user(
                        raw_password=password, superuser=is_superuser
                    )
                    if not pam_result.success and pam_result.return_code != 969:
                        raise PamError(pam_result)
                    elif pam_result.return_code == 969:
                        msg = _("User {} password setting error.").format(username)
                        await system_logger.warning(
                            message=msg,
                            entity={
                                "entity_type": EntityType.USER,
                                "entity_uuid": None,
                            },
                            user=creator,
                            description=pam_result,
                        )
                        await user_obj.deactivate(creator)
        except (PamError, UniqueViolationError) as err_msg:
            msg = _("User {} creation error.").format(username)
            await system_logger.error(
                message=msg,
                entity={"entity_type": EntityType.USER, "entity_uuid": None},
                user=creator,
                description=err_msg,
            )
            raise AssertionError(msg)

        user_role = _("Superuser.") if is_superuser else _("User.")
        info_message = _("{} {} created.").format(user_role[:-1], username)
        await system_logger.info(info_message, entity=user_obj.entity, user=creator)

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
    ):
        try:
            async with db.transaction():
                update_type, update_dict = await super().soft_update(
                    id,
                    email=email,
                    last_name=last_name,
                    first_name=first_name,
                    is_superuser=is_superuser,
                    creator=creator,
                )
                if PAM_AUTH:
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
                    if not pam_result.success:
                        raise PamError(pam_result)

        except PamError as err_msg:
            msg = _("User {} update error.").format(update_type.username)
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
            _("Values of user {} is changed.").format(update_type.username),
            description=desc,
            user=creator,
            entity=update_type.entity,
        )

        if "is_superuser" in update_dict and update_dict.get("is_superuser"):
            assigned_roles = _("Roles: {}.".format(str(await update_type.roles)))
            info_message = _("User {username} has become a superuser.").format(
                username=update_type.username
            )
            await system_logger.info(
                info_message,
                entity=update_type.entity,
                description=assigned_roles,
                user=creator,
            )
        elif update_dict.get("is_superuser") is False:
            assigned_roles = _("Roles: {}.".format(str(await update_type.roles)))
            info_message = _("User {username} is no longer a superuser.").format(
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
        await UserJwtInfo.soft_create(user_id=user.id, token=token)

        # Login event
        auth_type = "Ldap" if ldap else "Local"
        info_message = _("User {username} has been logged in.").format(
            username=username
        )
        description = _("Auth type: {}, IP: {}.").format(auth_type, ip)
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

        info_message = _("User {username} has been logged out.").format(
            username=username
        )
        await system_logger.info(info_message, entity=user.entity)
        return True


class UserJwtInfo(db.Model):
    """
    При авторизации пользователя выполняется запись.
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
    async def possible_users(self):
        """Берем всех АКТИВНЫХ пользователей и исключаем тех, кому уже назначена группа."""
        possible_users_query = (
            User.join(
                UserGroup.query.where(UserGroup.group_id == self.id).alias(),
                isouter=True,
            )
            .select()
            .where((text("anon_1.id is null")) & (User.is_active))
        )  # noqa
        return await possible_users_query.order_by(User.username).gino.load(User).all()

    @property
    def assigned_users_query(self):
        return User.join(
            UserGroup.query.where(UserGroup.group_id == self.id).alias()
        ).select()

    @property
    async def assigned_users(self):
        return await self.assigned_users_query.gino.load(User).all()

    async def assigned_users_paginator(self, limit, offset):
        return (
            await self.assigned_users_query.limit(limit)
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
        info_message = _("Group {} is created.").format(verbose_name)
        await system_logger.info(info_message, user=creator, entity=group_obj.entity)

        return group_obj

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
                        _("Group {} already has permission {}.").format(
                            self.id, permission
                        ),
                        user=creator,
                    )

        permissions_str = ", ".join(permissions_list)
        await system_logger.info(
            _("Permission(s) {} added to group {}.").format(
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
                _("Permission(s) {} removed from group {}.").format(
                    permissions_str, self.verbose_name
                ),
                user=creator,
                entity=self.entity,
            )

            assigned_permissions = await self.get_permissions()
            await system_logger.debug(
                _("Group {} permission(s): {}.").format(
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
                _("Values of group {} is updated.").format(self.verbose_name),
                description=desc,
                user=creator,
                entity=self.entity,
            )

        return self

    async def add_user(self, user_id, creator):
        """Add user to group"""
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
            user = await User.get(user_id)
            info_message = _("User {} has been included to group {}.").format(
                user.username, self.verbose_name
            )
            await system_logger.info(info_message, entity=self.entity, user=creator)
            return user_group
        except UniqueViolationError:
            raise SimpleError(
                _("User {} is already in group {}.").format(user_id, self.id)
            )

    async def add_users(self, user_id_list, creator):
        async with db.transaction():
            for user in user_id_list:
                await self.add_user(user, creator)

    async def remove_users(self, creator: str, user_id_list: list):
        for id in user_id_list:
            name = await User.get(id)
            await system_logger.info(
                _("Removing user {} from group {}.").format(
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
            info_message = _("Role {} has been set to group {}.").format(
                role, self.verbose_name
            )
            await system_logger.info(info_message, entity=self.entity, user=creator)

        except UniqueViolationError:
            raise SimpleError(
                _("Group {} has already role {}.").format(self.id, role), user=creator
            )
        return group_role

    async def add_roles(self, roles_list, creator):
        async with db.transaction():
            for role in roles_list:
                await self.add_role(role, creator)

    async def remove_roles(self, roles_list, creator):
        role_del = " ".join(roles_list)
        await system_logger.info(
            _("Roles: {} was deleted to group {}.").format(role_del, self.verbose_name),
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
