# -*- coding: utf-8 -*-
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy import Index
from sqlalchemy import Enum as AlchemyEnum
from asyncpg.exceptions import UniqueViolationError

from database import db, AbstractSortableStatusModel, Role, EntityType, AbstractClass
from auth.utils import hashers
from common.veil_errors import SimpleError

from languages import lang_init
from journal.journal import Log as log

_ = lang_init()


class Entity(db.Model):
    """
    entity_type: тип сущности из Enum
    entity_uuid: UUID сущности, если в качестве EntityType указано название таблицы  # TODO: rename to object_uuid
    """
    __tablename__ = 'entity'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_type = db.Column(AlchemyEnum(EntityType), nullable=False, index=True, default=EntityType.SYSTEM)
    entity_uuid = db.Column(UUID(), nullable=True, index=True)


class EntityRoleOwner(db.Model):
    """Ограничение прав доступа к сущности для конкретного типа роли.
       Если user_id и group_id null, то ограничение доступа к сущности только по Роли
       Если role пустой, то только по пользователю"""
    __tablename__ = 'entity_role_owner'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(), db.ForeignKey(Entity.id, ondelete="CASCADE"))
    role = db.Column(AlchemyEnum(Role), nullable=True, index=True)  # TODO: заменить на array?
    user_id = db.Column(UUID(), db.ForeignKey('user.id', ondelete="CASCADE"), nullable=True)
    group_id = db.Column(UUID(), db.ForeignKey('group.id', ondelete="CASCADE"), nullable=True)


class User(AbstractSortableStatusModel, AbstractClass):
    __tablename__ = 'user'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
    email = db.Column(db.Unicode(length=256), unique=False, nullable=True)
    last_name = db.Column(db.Unicode(length=128))
    first_name = db.Column(db.Unicode(length=32))
    date_joined = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    last_login = db.Column(db.DateTime(timezone=True), server_default=func.now())
    is_superuser = db.Column(db.Boolean(), default=False)
    is_active = db.Column(db.Boolean(), default=True)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    async def assigned_groups(self):
        groups = await Group.join(UserGroup.query.where(UserGroup.user_id == self.id).alias()).select().gino.load(
            Group).all()
        return groups

    @property
    async def assigned_groups_ids(self):
        groups = await UserGroup.select('group_id').where(UserGroup.user_id == self.id).gino.all()
        groups_ids_list = [group.group_id for group in groups]
        return groups_ids_list

    @property
    async def possible_groups(self):
        possible_groups_query = Group.join(UserGroup.query.where(UserGroup.user_id == self.id).alias(), isouter=True).select().where(text('anon_1.id is null'))  # noqa
        return await possible_groups_query.gino.load(User).all()

    @property
    async def roles(self):
        if self.is_superuser:
            all_roles_set = set(Role)  # noqa
            # log.debug(_('User: {} full roles: {}').format(self.username, all_roles_set))
            return all_roles_set

        user_roles = await UserRole.query.where(UserRole.user_id == self.id).gino.all()
        all_roles_list = [role_type.role for role_type in user_roles]

        # log.debug(_('User {} roles: {}').format(self.username, all_roles_list))

        user_groups = await self.assigned_groups
        for group in user_groups:
            group_roles = await group.roles
            # log.debug(_('Group {} roles: {}').format(group.verbose_name, group_roles))
            all_roles_list += [role_type.role for role_type in group_roles]

        roles_set = set(all_roles_list)
        # Сейчас роли будет в случайноп порядке.
        # log.debug(_('User: {} full roles: {}').format(self.username, roles_set))
        return roles_set

    @property
    async def pools(self):
        # Либо размещать staticmethod в пулах, либо импорт тут, либо хардкодить названия полей.
        from pool.models import Pool

        if self.is_superuser:
            # superuser есть все роли - мы просто выбираем все доступные пулы.
            pools_query = Pool.get_pools_query()
        else:
            user_roles = await self.roles
            user_groups_ids = await self.assigned_groups_ids
            pools_query = Pool.get_pools_query(user_id=self.id, groups_ids_list=user_groups_ids, role_set=user_roles)

        pools = await pools_query.gino.all()

        pools_list = [
            {'id': str(pool.master_id), 'name': pool.verbose_name, 'os_type': pool.os_type, 'status': pool.status.value,
             'connection_types': [connection_type.value for connection_type in pool.connection_types]}
            for pool in pools]

        return pools_list

    @staticmethod
    async def get_id(username):
        return await User.select('id').where(User.username == username).gino.scalar()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    async def add_role(self, role, creator):
        try:
            await log.info(_('Role {} is added to user {}').format(role, self.username), user=creator)
            add = await UserRole.create(user_id=self.id, role=role)
            user = await self.get(self.id)
            assigned_roles = await user.roles
            log.debug(_('User {} roles: {}').format(user.username, assigned_roles))
            return add
        except UniqueViolationError:
            raise SimpleError(_('Role {} is assigned to user {}').format(role, self.id), user=creator)

    async def remove_roles(self, roles_list=None, creator='system'):
        if not roles_list:
            return await UserRole.delete.where(UserRole.user_id == self.id).gino.status()
        if roles_list and isinstance(roles_list, list):
            role_del = ' '.join(roles_list)
            await log.info(_('Roles: {} was deleted to user {}').format(role_del, self.username), user=creator)
            remove = await UserRole.delete.where(
                (UserRole.role.in_(roles_list)) & (UserRole.user_id == self.id)).gino.status()
            user = await self.get(self.id)
            assigned_roles = await user.roles
            log.debug(_('User {} roles: {}').format(user.username, assigned_roles))
            return remove

    async def remove_groups(self):
        groups = await self.assigned_groups
        users_list = [self.id]
        for group in groups:
            await group.remove_users(users_list)
            await log.info(_('Group {} is removed for user {}').format(group, self.username))

    async def activate(self, creator):
        query = User.update.values(is_active=True).where(User.id == self.id)
        operation_status = await query.gino.status()

        info_message = _('User {username} has been activated.').format(username=self.username)
        await log.info(info_message, entity_dict=self.entity, user=creator)

        return operation_status

    async def deactivate(self, creator):
        """Деактивировать всех суперпользователей в системе - нельзя."""
        query = db.select([db.func.count(User.id)]).where(
            (User.id != self.id) & (User.is_superuser == True) & (User.is_active == True))  # noqa

        superuser_count = await query.gino.scalar()
        if superuser_count == 0:
            raise SimpleError(_('There is no more active superuser.'), user=creator)

        query = User.update.values(is_active=False).where(User.id == self.id)
        operation_status = await query.gino.status()

        info_message = _('User {username} has been deactivated.').format(username=self.username)
        await log.info(info_message, entity_dict=self.entity, user=creator)

        return operation_status

    @staticmethod
    async def check_email(email):
        email_count = await db.select([db.func.count()]).where(User.email == email).gino.scalar()
        return email_count < 1

    @staticmethod
    async def check_user(username, raw_password):
        count = await db.select([db.func.count()]).where(
            (User.username == username) & (User.is_active == True)).gino.scalar()  # noqa
        if count == 0:
            return False
        return await User.check_password(username, raw_password)

    @staticmethod
    async def check_password(username, raw_password):
        password = await User.select('password').where(User.username == username).gino.scalar()
        return await hashers.check_password(raw_password, password)

    async def set_password(self, raw_password, creator):
        encoded_password = hashers.make_password(raw_password)
        user_status = await User.update.values(password=encoded_password).where(
            User.id == self.id).gino.status()

        info_message = _('Password of user {username} has been changed.').format(username=self.username)
        await log.info(info_message, entity_dict=self.entity, user=creator)

        return user_status

    @classmethod
    async def soft_create(cls, username, creator, password=None, email=None, last_name=None, first_name=None, is_superuser=False,
                          id=None, is_active=True):
        """Если password будет None, то make_password вернет unusable password"""
        encoded_password = hashers.make_password(password)
        user_kwargs = {'username': username, 'password': encoded_password, 'email': email, 'last_name': last_name,
                       'first_name': first_name, 'is_superuser': is_superuser, 'is_active': is_active}
        if id:
            user_kwargs['id'] = id

        user_obj = await cls.create(**user_kwargs)

        user_role = 'Superuser' if is_superuser else 'User'
        info_message = _('User {} created with role {}.').format(username, user_role)
        await log.info(info_message, entity_dict=user_obj.entity, user=creator)

        return user_obj

    @classmethod
    async def soft_update(cls, id, **kwargs):
        update_type, update_dict = await super().soft_update(id, **kwargs)

        creator = update_dict.pop('creator')
        desc = str(update_dict)
        await log.info(_('Values of user {} is changed').format(update_type.username),
                       description=desc,
                       user=creator
                       )

        if 'is_superuser' in update_dict and update_dict.get('is_superuser'):
            assigned_roles = _('Roles: {}'.format(str(await update_type.roles)))
            info_message = _('User {username} has become a superuser.').format(username=update_type.username)
            await log.info(info_message, entity_dict=update_type.entity, description=assigned_roles, user=creator)
        elif update_dict.get('is_superuser') is False:
            assigned_roles = _('Roles: {}'.format(str(await update_type.roles)))
            info_message = _('User {username} has left a superuser.').format(username=update_type.username)
            await log.info(info_message, entity_dict=update_type.entity, description=assigned_roles, user=creator)

        return update_type

    @classmethod
    async def login(cls, username, token, client_type, ip=None, ldap=False):
        """Записывает данные с которыми пользователь вошел в систему"""
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        if not user:
            return False

        await user.update(last_login=func.now()).apply()
        await UserJwtInfo.soft_create(user_id=user.id, token=token)

        # Login event
        auth_type = 'Ldap' if ldap else 'Local'
        info_message = _('{auth_type}: user {username} has been logged in successfully. IP: {ip}.').format(
            auth_type=auth_type,
            username=username,
            ip=ip)

        await log.info(info_message, entity_dict=user.entity)
        return True

    @classmethod
    async def logout(cls, username, access_token):
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        if not user:
            return False
        # Проверяем, что нет попытки прервать запрещенный ранее токен
        is_valid = await UserJwtInfo.check_token(username, access_token)
        if not is_valid:
            return False

        # Запрещаем все выданные пользователю токены (Может быть только 1)
        await UserJwtInfo.delete.where(UserJwtInfo.user_id == user.id).gino.status()

        info_message = _('User {username} has logged out.').format(username=username)
        await log.info(info_message, entity_dict=user.entity)
        return True


class UserJwtInfo(db.Model):
    """
    При авторизации пользователя выполняется запись.
    В поле last_changed хранится дата последнего изменения токена. При изменении пароля/логауте/перегенерации токена
    значение поля меняется, вследствие чего токены, сгенерированные с помощью старых значений
    становятся невалидными.
    """
    __tablename__ = 'user_jwtinfo'

    user_id = db.Column(UUID(), db.ForeignKey(User.id, ondelete="CASCADE"), primary_key=True)
    # не хранит в себе 'jwt ' максимальный размер намеренно не установлен, т.к. четкого ограничение в стандарте нет.
    token = db.Column(db.Unicode(), nullable=False, index=True)
    last_changed = db.Column(db.DateTime(timezone=True), server_default=func.now())

    @classmethod
    async def soft_create(cls, user_id, token):
        # Не нашел в GINO create_or_update.

        count = await db.select([db.func.count()]).where(
            UserJwtInfo.user_id == user_id).gino.scalar()
        if count == 0:
            # Если записи для пользователя нет - создаем новую.
            await UserJwtInfo.create(user_id=user_id, token=token)
            return True
        # Если запись уже существует - обновлям значение токена.
        await UserJwtInfo.update.values(token=token, last_changed=func.now()).where(
            UserJwtInfo.user_id == user_id).gino.status()
        return True

    @classmethod
    async def check_token(cls, username, token):
        """Проверяет соответствие выданного токена тому, что пришел в payload."""
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        if not user:
            return False
        count = await db.select([db.func.count()]).where(
            (UserJwtInfo.user_id == user.id) & (UserJwtInfo.token == token)).gino.scalar()
        return count > 0


class Group(AbstractSortableStatusModel, AbstractClass):
    __tablename__ = 'group'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    description = db.Column(db.Unicode(length=255), nullable=True, unique=False)
    date_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    # На тестовых серверах были проблемы с форматом в AuthenticationDirectory.
    ad_guid = db.Column(db.Unicode(length=36), nullable=True, unique=True)

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:

    @property
    async def roles(self):
        query = GroupRole.select('role').where(GroupRole.group_id == self.id)
        return await query.gino.all()

    @property
    async def assigned_users(self):
        users_query = User.join(UserGroup.query.where(UserGroup.group_id == self.id).alias()).select()
        return await users_query.gino.load(User).all()

    @property
    async def possible_users(self):
        """Берем всех АКТИВНЫХ пользователей и исключаем тех, кому уже назначена группа."""
        possible_users_query = User.join(
            UserGroup.query.where(UserGroup.group_id == self.id).alias(), isouter=True).select().where(
            (text('anon_1.id is null')) & (User.is_active))  # noqa
        return await possible_users_query.order_by(User.username).gino.load(User).all()

    @staticmethod
    async def soft_create(verbose_name, creator, description=None, id=None, ad_guid=None):
        group_kwargs = {'verbose_name': verbose_name, 'description': description}
        if ad_guid:
            group_kwargs['ad_guid'] = str(ad_guid)
        if id:
            group_kwargs['id'] = id
        group_obj = await Group.create(**group_kwargs)
        info_message = _('Group {} is created.').format(verbose_name)
        await log.info(info_message, user=creator)

        return group_obj

    async def soft_update(self, verbose_name, description, creator):
        group_kwargs = dict()
        if verbose_name:
            group_kwargs['verbose_name'] = verbose_name
        if description:
            group_kwargs['description'] = description

        if group_kwargs:
            await self.update(**group_kwargs).apply()
            descr = str(group_kwargs)
            await log.info(_('Values of group {} is updated').format(self.verbose_name), description=descr, user=creator)

        return self

    async def add_user(self, user_id, creator):
        """Add user to group"""
        try:
            user_group = await UserGroup.create(user_id=user_id, group_id=self.id)

            user = await User.get(user_id)
            info_message = _('User {} has been included to group {}.').format(user.username, self.verbose_name)
            await log.info(info_message, entity_dict=self.entity, user=creator)
            return user_group
        except UniqueViolationError:
            raise SimpleError(_('User {} is already in group {}').format(user_id, self.id), user=creator)

    async def remove_users(self, user_id_list, creator):
        for id in user_id_list:
            name = await User.get(id)
            await log.info(_('Removing user {} from group {}').format(name.username, self.verbose_name), user=creator)
        return await UserGroup.delete.where(
            (UserGroup.user_id.in_(user_id_list)) & (UserGroup.group_id == self.id)).gino.status()

    async def add_role(self, role, creator):
        try:
            group_role = await GroupRole.create(group_id=self.id, role=role)
            info_message = _('Role {} has been set to group {}.').format(role, self.verbose_name)
            await log.info(info_message, entity_dict=self.entity, user=creator)

        except UniqueViolationError:
            raise SimpleError(_('Group {} has already role {}').format(self.id, role), user=creator)
        return group_role

    async def remove_roles(self, roles_list, creator):
        role_del = ' '.join(roles_list)
        await log.info(_('Roles: {} was deleted to group {}').format(role_del, self.verbose_name), user=creator)
        return await GroupRole.delete.where(
            (GroupRole.role.in_(roles_list)) & (GroupRole.group_id == self.id)).gino.status()


class UserGroup(db.Model):
    __tablename__ = 'user_groups'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(), db.ForeignKey(User.id, ondelete="CASCADE"), nullable=False)
    group_id = db.Column(UUID(), db.ForeignKey(Group.id, ondelete="CASCADE"), nullable=False)


class GroupRole(db.Model):
    __tablename__ = 'group_role'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    role = db.Column(AlchemyEnum(Role), nullable=False, index=True)
    group_id = db.Column(UUID(), db.ForeignKey(Group.id, ondelete="CASCADE"), nullable=False)


class UserRole(db.Model):
    __tablename__ = 'user_role'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    role = db.Column(AlchemyEnum(Role), nullable=False, index=True)
    user_id = db.Column(UUID(), db.ForeignKey(User.id, ondelete="CASCADE"), nullable=False)


# -------- Составные индексы --------------------------------
Index('ix_entity_entity_object_entity_type', Entity.entity_uuid, Entity.entity_type, unique=True)

Index('ix_user_in_group', UserGroup.user_id, UserGroup.group_id, unique=True)
Index('ix_user_roles_user_roles',
      UserRole.role, UserRole.user_id, unique=True)
Index('ix_group_roles_group_roles',
      GroupRole.role, GroupRole.group_id, unique=True)

Index('ix_entity_role_owner_entity_role_user',
      EntityRoleOwner.entity_id, EntityRoleOwner.role,
      EntityRoleOwner.user_id, unique=True)
Index('ix_entity_role_owner_entity_role_group',
      EntityRoleOwner.entity_id, EntityRoleOwner.role,
      EntityRoleOwner.group_id, unique=True)
Index('ix_entity_role_owner_entity_role_owner',
      EntityRoleOwner.entity_id, EntityRoleOwner.role,
      EntityRoleOwner.group_id, EntityRoleOwner.user_id, unique=True)
