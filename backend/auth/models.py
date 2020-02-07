# -*- coding: utf-8 -*-
import uuid
from typing import List
from enum import Enum
import logging

import ldap
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy import Index
from sqlalchemy import Enum as AlchemyEnum
from asyncpg.exceptions import UniqueViolationError

from settings import LDAP_TIMEOUT
from database import db, Status, AbstractSortableStatusModel, AbstractEntity, Role
from auth.utils import hashers
from event.models import Event
from common.veil_errors import SimpleError


application_log = logging.getLogger('tornado.application')


class EnityType(Enum):
    """Базовые виды сущностей"""
    # TODO: перечислить явно возможные виды сущностей
    # ANGULAR_WEB
    # THIN_CLIENT
    # CONTROLLER
    # LOCAL_AUTH
    # Security?
    # AutomatedPool
    # Pool
    pass


class Permission(Enum):
    VIEW = 'VIEW'
    ADD = 'ADD'
    CHANGE = 'CHANGE'
    DELETE = 'DELETE'


class Entity(db.Model):
    __tablename__ = 'entity'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_uuid = db.Column(UUID(), nullable=True, index=True)  # UUID сущности
    entity_type = db.Column(db.Unicode(), index=True)  # тип сущности (таблица в БД или абстрактная сущность)


class RoleEntityPermission(db.Model):

    __tablename__ = 'role_entity_permission'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    permission = db.Column(AlchemyEnum(Permission), nullable=False, index=True)
    role = db.Column(AlchemyEnum(Role), nullable=False, index=True)
    entity_id = db.Column(UUID(), db.ForeignKey(Entity.id, ondelete="CASCADE"))


class User(AbstractSortableStatusModel, db.Model, AbstractEntity):
    __tablename__ = 'user'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    password = db.Column(db.Unicode(length=128), nullable=False)
    email = db.Column(db.Unicode(length=256), unique=False, nullable=True)  # TODO: включить обратно после получения email из AD.
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
    def entity_type(self):
        return 'Security'

    @property
    async def groups(self):
        groups = await Group.join(UserGroup.query.where(UserGroup.user_id == self.id).alias()).select().gino.load(
            Group).all()
        return groups

    @property
    async def roles(self):
        if self.is_superuser:
            all_roles_set = set(Role)  # noqa
            application_log.debug('User: {} full roles: {}'.format(self.username, all_roles_set))
            return all_roles_set

        user_roles = await UserRole.query.where(UserRole.user_id == self.id).gino.all()
        all_roles_list = [role_type.role for role_type in user_roles]

        application_log.debug('User {} roles: {}'.format(self.username, all_roles_list))

        user_groups = await self.groups
        for group in user_groups:
            group_roles = await group.roles
            application_log.debug('Group {} roles: {}'.format(group.verbose_name, group_roles))
            all_roles_list += [role_type.role for role_type in group_roles]

        roles_set = set(all_roles_list)
        application_log.debug('User: {} full roles: {}'.format(self.username, roles_set))
        return roles_set

    @staticmethod
    async def get_id(username):
        return await User.select('id').where(User.username == username).gino.scalar()

    # ----- ----- ----- ----- ----- ----- -----
    # Setters & etc.

    async def add_role(self, role):
        try:
            return await UserRole.create(user_id=self.id, role=role)
        except UniqueViolationError:
            raise SimpleError('Пользователю {} уже назначена роль {}'.format(self.id, role))

    async def add_roles(self, roles_list):
        async with db.transaction():
            for role in roles_list:
                await self.add_role(role)

    async def remove_roles(self, roles_list):
        return await UserRole.delete.where(
            (UserRole.role.in_(roles_list)) & (UserRole.user_id == self.id)).gino.status()

    async def activate(self):
        query = User.update.values(is_active=True).where(User.id == self.id)
        operation_status = await query.gino.status()

        info_message = 'User {username} has been activated.'.format(username=self.username)
        await Event.create_info(info_message, entity_list=self.entity_list)

        return operation_status

    async def deactivate(self):
        # TODO: проверка, сколько останется активных администраторов не с этим id
        query = db.select([db.func.count(User.id)]).where(
            (User.id != self.id) & (User.is_superuser == True) & (User.is_active == True))  # noqa

        superuser_count = await query.gino.scalar()
        if superuser_count == 0:
            raise SimpleError('There is no more active superuser. Leg shot.')

        query = User.update.values(is_active=False).where(User.id == self.id)
        operation_status = await query.gino.status()

        info_message = 'User {username} has been deactivated.'.format(username=self.username)
        await Event.create_info(info_message, entity_list=self.entity_list)

        return operation_status

    @staticmethod
    async def check_password(username, raw_password):
        password = await User.select('password').where(User.username == username).gino.scalar()
        return await hashers.check_password(raw_password, password)

    @staticmethod
    async def check_user(username, raw_password):
        count = await db.select([db.func.count()]).where(
            (User.username == username) & (User.is_active == True)).gino.scalar()  # noqa
        if count == 0:
            return False
        return await User.check_password(username, raw_password)

    async def set_password(self, raw_password):
        encoded_password = hashers.make_password(raw_password)
        user_status = await User.update.values(password=encoded_password).where(
            User.id == self.id).gino.status()

        info_message = 'Password of user {username} has been changed.'.format(username=self.username)
        await Event.create_info(info_message, entity_list=self.entity_list)

        return user_status

    @staticmethod
    async def soft_create(username, password=None, email=None, last_name=None, first_name=None, is_superuser=False):
        """Если password будет None, то make_password вернет unusable password"""
        encoded_password = hashers.make_password(password)
        user_obj = await User.create(username=username, password=encoded_password, email=email, last_name=last_name,
                                     first_name=first_name, is_superuser=is_superuser)

        user_role = 'Superuser' if is_superuser else 'User'
        info_message = 'Creating user {username} with role {role}.'.format(username=username, role=user_role)
        await Event.create_info(info_message, entity_list=user_obj.entity_list)

        return user_obj

    @classmethod
    async def soft_update(cls, user_id, username, email, last_name, first_name, is_superuser):
        user_kwargs = dict()
        if username:
            user_kwargs['username'] = username
        if email:
            user_kwargs['email'] = email
        if last_name:
            user_kwargs['last_name'] = last_name
        if first_name:
            user_kwargs['first_name'] = first_name
        if is_superuser or is_superuser is False:
            user_kwargs['is_superuser'] = is_superuser
        if user_kwargs:
            await User.update.values(**user_kwargs).where(
                User.id == user_id).gino.status()
        user = await User.get(user_id)

        if user_kwargs.get('is_superuser'):
            info_message = 'User {username} has become a superuser.'.format(username=user.username)
            await Event.create_info(info_message, entity_list=user.entity_list)

        return user

    @classmethod
    async def login(cls, username, token, client_type, ip=None, ldap=False):
        """Записывает данные с которыми пользователь вошел в систему"""
        user = await User.get_object(extra_field_name='username', extra_field_value=username)
        if not user:
            return False
        await user.update(last_login=func.now()).apply()
        await UserJwtInfo.soft_create(user_id=user.id, token=token)

        # Login event
        info_message = 'User {username} has been logged in successfully. IP address: {ip}.'.format(username=username,
                                                                                                   ip=ip)
        entity_list = list()
        entity_list.append({'entity_type': user.entity_type, 'entity_uuid': user.uuid})
        entity_list.append({'entity_type': client_type, 'entity_uuid': user.uuid})
        entity_list.append(
            {'entity_type': 'LDAP_AUTH' if ldap else 'LOCAL_AUTH', 'entity_uuid': user.uuid})

        await Event.create_info(info_message, entity_list=entity_list)
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

        # Запрещаем все выданные пользователю токены (Сейчас может быть только 1)
        await UserJwtInfo.delete.where(UserJwtInfo.user_id == user.id).gino.status()

        info_message = 'User {username} has logged out.'.format(username=username)
        await Event.create_info(info_message, entity_list=user.entity_list)
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


class Group(AbstractSortableStatusModel, db.Model, AbstractEntity):
    __tablename__ = 'group'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    description = db.Column(db.Unicode(length=255), nullable=True, unique=False)
    date_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    date_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    # ----- ----- ----- ----- ----- ----- -----
    # Properties and getters:
    @property
    def entity_type(self):
        return 'Security'

    @property
    async def roles(self):
        query = GroupRole.select('role').where(GroupRole.group_id == self.id)
        return await query.gino.all()

    async def add_user(self, user_id):
        """Add user to group"""
        try:
            return await UserGroup.create(user_id=user_id, group_id=self.id)
        except UniqueViolationError:
            raise SimpleError('Пользователь {} уже находится в группе {}'.format(user_id, self.id))

    async def add_users(self, user_id_list):
        async with db.transaction():
            for user in user_id_list:
                await self.add_user(user)

    async def remove_users(self, user_id_list):
        return await UserGroup.delete.where(
            (UserGroup.user_id.in_(user_id_list)) & (UserGroup.group_id == self.id)).gino.status()

    async def add_role(self, role):
        try:
            return await GroupRole.create(group_id=self.id, role=role)
        except UniqueViolationError:
            raise SimpleError('Группе {} уже назначена роль {}'.format(self.id, role))

    async def add_roles(self, roles_list):
        async with db.transaction():
            for role in roles_list:
                await self.add_role(role)

    async def remove_roles(self, roles_list):
        return await GroupRole.delete.where(
            (GroupRole.role.in_(roles_list)) & (GroupRole.group_id == self.id)).gino.status()

    async def soft_update(self, verbose_name, description):
        group_kwargs = dict()
        if verbose_name:
            group_kwargs['verbose_name'] = verbose_name
        if description:
            group_kwargs['description'] = description

        if group_kwargs:
            await self.update(**group_kwargs).apply()

        return self


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


class AuthenticationDirectory(db.Model, AbstractSortableStatusModel, AbstractEntity):
    """
    Модель служб каталогов для авторизации пользователей в системе.
    Не может быть более 1го.
    Описание полей:

    - connection_type: тип подключения (поддерживается только LDAP)
    - description: описание объекта
    - directory_url: адрес службы каталогов
    - directory_type: тип службы каталогов (поддерживается только MS Active Directory)
    - domain_name: имя контроллера доменов
    - verbose_name: имя объекта, назначенное пользователем
    - service_username: username имеющий права для управления AD
    - service_password: password
    - admin_server: url сервера управления AD
    - kdc_urls: список всех url'ов Key Distributed Centers
    - sso: Технология Single Sign-on
    """

    class ConnectionTypes(Enum):
        """
        Класс, описывающий доступные типы подключения служб каталогов.
        """

        LDAP = 'LDAP'

    class DirectoryTypes(Enum):
        """
        Класс, описывающий доступные типы служб каталогов.
        """

        ActiveDirectory = 'ActiveDirectory'

    __tablename__ = 'authentication_directory'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=255), unique=True)
    connection_type = db.Column(AlchemyEnum(ConnectionTypes), nullable=False, server_default=ConnectionTypes.LDAP.value)
    description = db.Column(db.Unicode(length=255), nullable=True)
    directory_url = db.Column(db.Unicode(length=255))
    directory_type = db.Column(AlchemyEnum(DirectoryTypes), nullable=False,
                               server_default=DirectoryTypes.ActiveDirectory.value)
    domain_name = db.Column(db.Unicode(length=255), unique=True)
    subdomain_name = db.Column(db.Unicode(length=255))
    service_username = db.Column(db.Unicode(length=150), nullable=True)
    service_password = db.Column(db.Unicode(length=128), nullable=True)
    admin_server = db.Column(db.Unicode(length=255), nullable=True)
    kdc_urls = db.Column(ARRAY(db.Unicode(length=255)), nullable=True)
    sso = db.Column(db.Boolean(), default=False)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)

    async def test_connection(self) -> bool:
        """
        Метод тестирования соединения с сервером службы каталогов.

        :param directory_url: адрес службы каталогов
        :param connection_type: тип подключения
        :return: результат проверки соединения
        """
        if self.connection_type == self.ConnectionTypes.LDAP:
            try:
                ldap_server = ldap.initialize(self.directory_url)
                ldap_server.set_option(ldap.OPT_TIMEOUT, LDAP_TIMEOUT)
                ldap_server.simple_bind_s()
            except ldap.INVALID_CREDENTIALS:
                return True
            except ldap.SERVER_DOWN:
                msg = 'LDAP server {} is down.'.format(self.directory_url)
                application_log.warning(msg)
                await Event.create_warning(msg, entity_list=self.entity_list)
                return False
            return True
        msg = 'Can\'t connect to LDAP server {}.'.format(self.directory_url)
        application_log.warning(msg)
        await Event.create_warning(msg, entity_list=self.entity_list)
        return False

    @staticmethod
    def _extract_domain_from_username(username: str) -> List[str]:
        """
        Метод для разделения имени пользователя по символу @ на имя пользовательской учетной записи
        и доменное имя контроллера доменов.

        :param username: имя пользователя
        :return: список, содержащий имя пользователской учетной записи (sAMAccountName)
        и доменное имя контроллера доменов
        """
        splitted_list = username.split('@')
        if len(splitted_list) > 1:
            return splitted_list[:2]
        return splitted_list[0], None

    @classmethod
    async def soft_create(cls, verbose_name, directory_url, domain_name,
                          service_username=None,
                          service_password=None,
                          description=None, connection_type=ConnectionTypes.LDAP,
                          directory_type=DirectoryTypes.ActiveDirectory, admin_server=None,
                          subdomain_name=None, kdc_urls=None, sso=False):
        """Сначала создается контроллер домена в статусе Creating.
           Затем проверяется доступность и происходит смена статуса на ACTIVE."""

        count = await db.func.count(AuthenticationDirectory.id).gino.scalar()
        if count > 0:
            raise AssertionError('More than one authentication directory can not be created.')

        # TODO: crypto password
        auth_dir = await AuthenticationDirectory.create(verbose_name=verbose_name,
                                                        description=description,
                                                        directory_url=directory_url,
                                                        connection_type=connection_type,
                                                        directory_type=directory_type,
                                                        domain_name=domain_name,
                                                        service_username=service_username,
                                                        service_password=service_password,
                                                        admin_server=admin_server,
                                                        subdomain_name=subdomain_name,
                                                        kdc_urls=kdc_urls,
                                                        sso=sso,
                                                        status=Status.CREATING)
        connection_ok = await auth_dir.test_connection()
        if connection_ok:
            await auth_dir.update(status=Status.ACTIVE).apply()
        return auth_dir

    # @property
    # def keytab(self) -> Optional['Keytab']:
    #     # TODO: adapt for vdi
    #     return self.keytabs.first()
    #
    # @property
    # def sso_domain(self) -> str:
    #     # TODO: adapt for vdi
    #     return '.'.join([self.subdomain_name, self.domain_name])
    #
    # @classmethod
    # def has_upload_keytab_permission(cls, request):
    #     # TODO: adapt for vdi
    #     return cls.has_configure_sso_permission(request)
    #
    # @classmethod
    # def has_configure_sso_permission(cls, request):
    #     # TODO: adapt for vdi
    #     return cls.check_permission(request.user, 'configure_sso')
    #
    # @classmethod
    # def has_test_connection_permission(cls, request):
    #     # TODO: adapt for vdi
    #     return cls.check_permission(request.user, 'test_connection')

    @classmethod
    async def _get_user(cls, username: str):
        """
        Метод получения объекта пользователя из БД на основе его имени.
        Если пользователь не существует, то будет создан с пустым паролем.
        Авторизация этого пользователя возможна только по LDAP.

        :param username: имя пользователя
        :param kwargs: дополнительные именованные аргументы
        :return: объект пользователя, флаг создания пользователя
        """
        if not isinstance(username, str):
            raise AssertionError('Username must be a string.')

        username = username.lower()
        user = await User.get_object(extra_field_name='username', extra_field_value=username, include_inactive=True)
        if not user:
            user = await User.soft_create(username)
            created = True
        else:
            await user.update(is_active=True).apply()
            created = False
        return user, created

    @classmethod
    async def authenticate(cls, username, password):
        """
        Метод аутентификации пользователя на основе данных из службы каталогов.
        """
        success = False
        created = False

        authentication_directory = await AuthenticationDirectory.get_objects(first=True)
        if not authentication_directory:
            # Если для доменного имени службы каталогов не создано записей в БД,
            # то авторизоваться невозможно.
            raise AssertionError('No authentication directory controllers.')

        account_name, domain_name = cls._extract_domain_from_username(username)
        user, created = await cls._get_user(account_name)

        if not domain_name:
            domain_name = authentication_directory.domain_name
            username = '@'.join([username, domain_name])

        try:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            ldap_server = ldap.initialize(authentication_directory.directory_url)
            ldap_server.set_option(ldap.OPT_REFERRALS, 0)
            ldap_server.set_option(ldap.OPT_NETWORK_TIMEOUT, LDAP_TIMEOUT)
            ldap_server.simple_bind_s(username, password)
        except ldap.INVALID_CREDENTIALS:
            # Если пользователь не проходит аутентификацию в службе каталогов с предоставленными
            # данными, то аутентификация в системе считается неуспешной и создается событие с
            # сообщением о неуспешности.
            # self._create_user_auth_failed_event(user)
            success = False
            raise AssertionError('Invalid credeintials (ldap).')
        except ldap.SERVER_DOWN:
            # Если нет связи с сервером службы каталогов, то возвращаем ошибку о недоступности
            # сервера, так как не можем сделать вывод о правильности предоставленных данных.
            # self.server_down = True
            success = False
            raise AssertionError('Server down (ldap).')
        else:
            success = True
        finally:
            if not success and created:
                await user.delete()

    @classmethod
    async def soft_update(cls, id, verbose_name, directory_url, connection_type, description, directory_type,
                          domain_name, subdomain_name, service_username, service_password, admin_server, kdc_urls,
                          sso):
        object_kwargs = dict()
        if verbose_name:
            object_kwargs['verbose_name'] = verbose_name
        if directory_url:
            object_kwargs['directory_url'] = directory_url
        if connection_type:
            object_kwargs['connection_type'] = connection_type
        if description:
            object_kwargs['description'] = description
        if sso or sso is False:
            object_kwargs['sso'] = sso
        if directory_type:
            object_kwargs['directory_type'] = directory_type
        if domain_name:
            object_kwargs['domain_name'] = domain_name
        if subdomain_name:
            object_kwargs['subdomain_name'] = subdomain_name
        if service_username:
            object_kwargs['service_username'] = service_username
        if service_password:
            # TODO: password encryption
            object_kwargs['service_password'] = service_password
        if admin_server:
            object_kwargs['admin_server'] = admin_server
        if kdc_urls:
            object_kwargs['kdc_urls'] = kdc_urls

        if object_kwargs:
            await cls.update.values(**object_kwargs).where(
                cls.id == id).gino.status()
        return await cls.get(id)

    @classmethod
    async def soft_delete(cls, id):
        """Все удаления объектов AD необходимо делать тут."""
        # TODO: после ввода сущностей в Event, удалять зависимые записи журнала событий, возможно через ON_DELETE.
        auth_dir = await AuthenticationDirectory.get_object(id=id, include_inactive=True)
        if auth_dir:
            msg = 'Authentication Directory {name} deleted.'.format(name=auth_dir.verbose_name)
            await auth_dir.delete()
            await Event.create_info(msg)
            return True
        return False


# -------- Составные индексы --------------------------------
# Ограничение на включение пользователя в одну и ту же группу.
Index('ix_user_in_group', UserGroup.user_id, UserGroup.group_id, unique=True)
Index('ix_role_entity_permission_role_entity_permission',
      RoleEntityPermission.permission, RoleEntityPermission.role,
      RoleEntityPermission.entity_id, unique=True)
Index('ix_user_roles_user_roles',
      UserRole.role, UserRole.user_id, unique=True)
Index('ix_group_roles_group_roles',
      GroupRole.role, GroupRole.group_id, unique=True)
