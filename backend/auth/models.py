# -*- coding: utf-8 -*-
import uuid
from typing import List
from enum import Enum

import ldap
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import Enum as AlchemyEnum

from database import db, Status, AbstractSortableStatusModel
from user.models import User
from event.models import Event


class AuthenticationDirectory(db.Model, AbstractSortableStatusModel):
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
    # connection_type = db.Column(db.Unicode(length=4), nullable=False, server_default=ConnectionTypes.LDAP)
    connection_type = db.Column(AlchemyEnum(ConnectionTypes), nullable=False, server_default=ConnectionTypes.LDAP.value)
    description = db.Column(db.Unicode(length=255), nullable=True)
    directory_url = db.Column(db.Unicode(length=255))
    # directory_type = db.Column(db.Unicode(length=16), nullable=False, server_default=DirectoryTypes.ActiveDirectory)
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
                ldap_server.simple_bind_s()
            except ldap.INVALID_CREDENTIALS:
                return True
            except ldap.SERVER_DOWN:
                await Event.create_warning('Auth: LDAP server {} is down.'.format(self.directory_url))
                return False
            return True
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
            ldap_server.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
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
            msg = 'Authentication Directory {id} deleted.'.format(id=id)
            await auth_dir.delete()
            await Event.create_info(msg)
            return True
        return False

