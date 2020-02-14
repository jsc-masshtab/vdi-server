# -*- coding: utf-8 -*-
import uuid
from enum import Enum
from typing import List

import ldap
from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy import Index
from sqlalchemy.sql import text

from auth.models import application_log, User, Group
from database import db, AbstractSortableStatusModel, AbstractEntity, Status
from event.models import Event
from settings import LDAP_TIMEOUT


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

    # TODO: move to authentication_directory package

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

    @property
    async def mappings(self):
        query = Mapping.join(
            GroupAuthenticationDirectoryMapping.query.where(AuthenticationDirectory.id == self.id).alias()).select()
        return await query.gino.load(Mapping).all()

    # async def add_mapping(self, verbose_name, description, attribute, attribute_values, priority, groups):
    async def add_mapping(self, mapping: dict, groups: list):
        """
        :param mapping: Dictionary of Mapping table kwargs.
        :param groups: List of Group.id strings.
        """

        async with db.transaction():
            mapping_obj = await Mapping.create(**mapping)
            for group_id in groups:
                await GroupAuthenticationDirectoryMapping.create(authentication_directory_id=self.id,
                                                                 group_id=group_id, mapping_id=mapping_obj.id)

    async def edit_mapping(self, mapping: dict, groups: list):
        """
        :param mapping: Dictionary of Mapping table kwargs.
        :param groups: List of Group.id strings.
        """

        async with db.transaction():
            mapping_id = mapping.pop('mapping_id')
            mapping_obj = await Mapping.get(mapping_id)
            await mapping_obj.soft_update(**mapping)
            if groups:
                await GroupAuthenticationDirectoryMapping.delete.where(
                    GroupAuthenticationDirectoryMapping.mapping_id == mapping_id).gino.status()
                for group_id in groups:
                    await GroupAuthenticationDirectoryMapping.create(authentication_directory_id=self.id,
                                                                     group_id=group_id, mapping_id=mapping_id)

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
                          subdomain_name=None, kdc_urls=None, sso=False, id=None):
        """Сначала создается контроллер домена в статусе Creating.
           Затем проверяется доступность и происходит смена статуса на ACTIVE."""
        count = await db.func.count(AuthenticationDirectory.id).gino.scalar()
        if count > 0:
            raise AssertionError('More than one authentication directory can not be created.')

        auth_dir_dict = {'verbose_name': verbose_name,
                         'description': description,
                         'directory_url': directory_url,
                         'connection_type': connection_type,
                         'directory_type': directory_type,
                         'domain_name': domain_name,
                         'service_username': service_username,
                         'service_password': service_password,
                         'admin_server': admin_server,
                         'subdomain_name': subdomain_name,
                         'kdc_urls': kdc_urls,
                         'sso': sso,
                         'status': Status.CREATING
                         }
        if id:
            auth_dir_dict['id'] = id

        # TODO: crypto password
        auth_dir = await AuthenticationDirectory.create(**auth_dir_dict)
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
        except ldap.INVALID_CREDENTIALS as ldap_error:
            # Если пользователь не проходит аутентификацию в службе каталогов с предоставленными
            # данными, то аутентификация в системе считается неуспешной и создается событие с
            # сообщением о неуспешности.
            # self._create_user_auth_failed_event(user)
            success = False
            application_log.debug(ldap_error)
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


class Mapping(db.Model, AbstractEntity):
    """
    Модель отображения атрибутов пользователя службы каталогов на группы пользователей системы.
    Описание полей:

    - mapping_type: тип атрибута службы каталогов для отображения на группы системы
    - values: список значений атрибутов пользователя службы каталогов
    """
    __tablename__ = 'mapping'

    class ValueTypes(Enum):
        """
        Класс, описывающий доступные типы атрибутов службы каталогов.
        """

        USER = 'USER'
        OU = 'OU'
        GROUP = 'GROUP'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    description = db.Column(db.Unicode(length=255), nullable=True, unique=False)
    value_type = db.Column(AlchemyEnum(ValueTypes), nullable=False, index=True)
    values = db.Column(JSONB(), nullable=False)
    priority = db.Column(db.Integer(), nullable=False, default=0)

    @property
    async def assigned_groups(self):
        query = Group.join(
            GroupAuthenticationDirectoryMapping.query.where(
                GroupAuthenticationDirectoryMapping.mapping_id == self.id).alias()).select()
        return await query.gino.load(Group).all()

    @property
    async def possible_groups(self):
        possible_groups_query = Group.join(
            GroupAuthenticationDirectoryMapping.query.where(
                GroupAuthenticationDirectoryMapping.mapping_id == self.id).alias(),
            isouter=True).select().where(
            (text('anon_1.id is null'))
        )
        return await possible_groups_query.gino.load(Group).all()

    async def soft_update(self, verbose_name=None, description=None, value_type=None, values=None, priority=None):
        mapping_kwargs = dict()
        if verbose_name:
            mapping_kwargs['verbose_name'] = verbose_name
        if description:
            mapping_kwargs['description'] = description
        if value_type:
            mapping_kwargs['value_type'] = value_type
        if values:
            mapping_kwargs['values'] = values
        if priority:
            mapping_kwargs['priority'] = priority
        if mapping_kwargs:
            await Mapping.update.values(**mapping_kwargs).where(
                Mapping.id == self.id).gino.status()
        # TODO: edit groups!!
        return await Mapping.get(self.id)


class GroupAuthenticationDirectoryMapping(db.Model):
    __tablename__ = 'group_authentication_directory_mappings'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    authentication_directory_id = db.Column(UUID(),
                                            db.ForeignKey(AuthenticationDirectory.id, ondelete="CASCADE"),
                                            nullable=False)
    group_id = db.Column(UUID(),
                         db.ForeignKey(Group.id, ondelete="CASCADE"),
                         nullable=False)
    mapping_id = db.Column(UUID(),
                           db.ForeignKey(Mapping.id, ondelete="CASCADE"),
                           nullable=False)


Index('ix_group_auth_mapping', GroupAuthenticationDirectoryMapping.authentication_directory_id,
      GroupAuthenticationDirectoryMapping.group_id, GroupAuthenticationDirectoryMapping.mapping_id, unique=True)
