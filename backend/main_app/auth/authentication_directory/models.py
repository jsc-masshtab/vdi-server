# -*- coding: utf-8 -*-
import uuid
from enum import Enum
from typing import Tuple, Optional
import ldap
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy import Index, Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.sql import text, desc

from settings import LDAP_TIMEOUT
from database import db, AbstractSortableStatusModel, Status, Role, AbstractClass
from auth.utils.crypto import encrypt, decrypt
from auth.models import User, Group
from auth.authentication_directory.utils import (unpack_guid, pack_guid, unpack_ad_info,
                                                 extract_domain_from_username, get_ad_user_ou, get_ad_user_groups)
from languages import lang_init
from journal.journal import Log
from common.veil_errors import SimpleError, ValidationError


_ = lang_init()


class AuthenticationDirectory(AbstractClass, AbstractSortableStatusModel):
    """Модель служб каталогов для авторизации пользователей в системе.

    connection_type: тип подключения (поддерживается только LDAP)
    description: описание объекта
    directory_url: адрес службы каталогов
    directory_type: тип службы каталогов (поддерживается только MS Active Directory)
    domain_name: имя контроллера доменов
    verbose_name: имя объекта, назначенное пользователем
    service_username: username имеющий права для управления AD
    service_password: password
    admin_server: url сервера управления AD
    kdc_urls: список всех url'ов Key Distributed Centers
    sso: Технология Single Sign-on
    Не может быть более 1го.
    """

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

    class ConnectionTypes(Enum):
        """Доступные типы подключения служб каталогов."""

        LDAP = 'LDAP'

    class DirectoryTypes(Enum):
        """Доступные типы служб каталогов."""

        ActiveDirectory = 'ActiveDirectory'

    AD_GROUP_ID = 'objectGUID'
    AD_GROUP_NAME = 'cn'
    AD_USERNAME = 'sAMAccountName'
    AD_EMAIL = 'mail'
    AD_FULLNAME = 'displayName'
    AD_FIRST_NAME = 'givenName'
    AD_SURNAME = 'sn'

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
    # Из-за шифрования размер строки с паролем сильно увеличивается.
    service_password = db.Column(db.Unicode(length=1000), nullable=True)
    admin_server = db.Column(db.Unicode(length=255), nullable=True)
    kdc_urls = db.Column(ARRAY(db.Unicode(length=255)), nullable=True)
    sso = db.Column(db.Boolean(), default=False)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)

    @property
    def mappings_query(self):
        return Mapping.join(GroupAuthenticationDirectoryMapping.query.where(
            AuthenticationDirectory.id == self.id).alias()).select().order_by(desc(Mapping.priority))

    @property
    async def mappings(self):
        return await self.mappings_query.gino.load(Mapping).all()

    async def mappings_paginator(self, limit, offset):
        return await self.mappings_query.limit(limit).offset(offset).gino.load(Mapping).all()

    @classmethod
    async def soft_create(cls, verbose_name, directory_url, domain_name, creator,
                          service_username=None,
                          service_password=None,
                          description=None, connection_type=ConnectionTypes.LDAP,
                          directory_type=DirectoryTypes.ActiveDirectory, admin_server=None,
                          subdomain_name=None, kdc_urls=None, sso=False, id=None):
        """Создает запись Authentication Directory.
        Если не удалось проверить соединение - статус изменится на Failed."""
        # Ограничение на количество записей
        count = await db.func.count(AuthenticationDirectory.id).gino.scalar()
        if count > 0:
            raise SimpleError(_('More than one authentication directory can not be created.'), user=creator)
        # Шифруем пароль
        if service_password and isinstance(service_password, str):
            service_password = encrypt(service_password)

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
        # Создаем запись
        auth_dir = await AuthenticationDirectory.create(**auth_dir_dict)
        await Log.info(_('Authentication directory {} is created').format(auth_dir_dict.get('verbose_name')),
                       user=creator
                       )
        # Проверяем доступность
        await auth_dir.test_connection()
        return auth_dir

    @classmethod
    async def soft_update(cls, id, **kwargs):

        # TODO: password encryption
        update_type, update_dict = await super().soft_update(id, **kwargs)

        creator = update_dict.pop('creator')
        desc = str(update_dict)
        await Log.info(_('Values for auth directory is updated'), description=desc, user=creator)

        await update_type.test_connection()
        return update_type

    async def soft_delete(self, dest, creator):
        parent = super().soft_delete(dest, creator)

        # Удаляем у существующих групп все ad_guid
        await Group.update.values(ad_guid=None).where(Group.ad_guid.isnot(None)).gino.status()
        return parent

    async def add_mapping(self, mapping: dict, groups: list, creator):
        """
        :param mapping: Dictionary of Mapping table kwargs.
        :param groups: List of Group.id strings.
        """

        async with db.transaction():
            mapping_obj = await Mapping.create(**mapping)
            for group_id in groups:
                await GroupAuthenticationDirectoryMapping.create(authentication_directory_id=self.id,
                                                                 group_id=group_id, mapping_id=mapping_obj.id)
                group_name = await Group.get(group_id)
                desc = _('Arguments: {} of group: {}').format(mapping, group_name.verbose_name)
                msg = _('Mapping for auth directory {} is created').format(self.verbose_name)
                await Log.info(msg, description=desc, user=creator)

    async def edit_mapping(self, mapping: dict, groups: list, creator):
        """
        :param mapping: Dictionary of Mapping table kwargs.
        :param groups: List of Group.id strings.
        """
        async with db.transaction():
            mapping_id = mapping.pop('mapping_id')
            mapping_obj = await Mapping.get(mapping_id)
            await mapping_obj.soft_update(mapping_id, verbose_name=mapping.get('verbose_name'), description=mapping.get('description'),
                                          value_type=mapping.get('value_type'), values=mapping.get('values'),
                                          priority=mapping.get('priority'), creator=creator
                                          )
            if groups:
                await GroupAuthenticationDirectoryMapping.delete.where(
                    GroupAuthenticationDirectoryMapping.mapping_id == mapping_id).gino.status()
                for group_id in groups:
                    await GroupAuthenticationDirectoryMapping.create(authentication_directory_id=self.id,
                                                                     group_id=group_id, mapping_id=mapping_id)
                    group_name = await Group.get(group_id)
                    desc = _('New arguments: {} of group: {}').format(mapping, group_name.verbose_name)
                    msg = _('Mapping for auth directory {} is updated').format(self.verbose_name)
                    await Log.info(msg, description=desc, user=creator)

    async def test_connection(self) -> bool:
        """
        Метод тестирования соединения с сервером службы каталогов.
        :return: результат проверки соединения
        """
        try:
            ldap_server = ldap.initialize(self.directory_url)
            ldap_server.set_option(ldap.OPT_TIMEOUT, LDAP_TIMEOUT)
            # Если у записи есть данные auth - проверяем их
            if self.service_password or self.service_username:
                username = '@'.join([self.service_username, self.domain_name])
                password = decrypt(self.service_password)
                ldap_server.simple_bind_s(username, password)
            else:
                ldap_server.simple_bind_s()
        except (ldap.INVALID_CREDENTIALS, TypeError):
            await self.update(status=Status.BAD_AUTH).apply()
        except ldap.SERVER_DOWN:
            msg = _('Authentication directory server {} is down.').format(self.directory_url)
            await Log.warning(msg, entity_dict=self.entity)
            await self.update(status=Status.FAILED).apply()
            return False
        else:
            ldap_server.unbind_s()
            await self.update(status=Status.ACTIVE).apply()
        await Log.info(_('Authentication directory server {} is connected').format(self.directory_url))
        return True

    # Authentication Directory synchronization methods

    @staticmethod
    def _get_ad_user_attributes(account_name: str,
                                domain_name: str,
                                ldap_server: 'ldap.ldapobject.SimpleLDAPObject'
                                ) -> Tuple[Optional[str], dict]:
        """Получение информации о текущем пользователе из службы каталогов.

        :param account_name: имя пользовательской учетной записи
        :param domain_name: доменное имя контроллера доменов
        :param ldap_server: объект сервера службы каталогов
        :return: атрибуты пользователя службы каталогов
        """
        base = 'dc={},dc={}'.format(*domain_name.split('.'))
        user_info_filter = '(&(objectClass=user)(sAMAccountName={}))'.format(account_name)
        user_info, user_groups = ldap_server.search_s(base, ldap.SCOPE_SUBTREE,
                                                      user_info_filter, ['memberOf'])[0]

        return user_info, user_groups

    @classmethod
    async def _get_user(cls, username: str):
        """Получение объекта пользователя из БД на основе его имени.
        Если пользователь не существует, то будет создан с пустым паролем.
        Авторизация этого пользователя возможна только по LDAP.

        :param username: имя пользователя
        :param kwargs: дополнительные именованные аргументы
        :return: объект пользователя, флаг создания пользователя
        """
        if not isinstance(username, str):
            raise ValidationError(_('Username must be a string.'))

        username = username.lower()
        user = await User.get_object(extra_field_name='username', extra_field_value=username, include_inactive=True)
        if not user:
            user = await User.soft_create(username, creator='system')
            created = True
        else:
            await user.update(is_active=True).apply()
            created = False
        return user, created

    async def assign_veil_roles(self,
                                ldap_server: 'ldap.ldapobject.SimpleLDAPObject',
                                user: 'User',
                                account_name: str) -> bool:
        """
        Метод назначения пользователю системной группы на основе атрибутов его учетной записи
        в службе каталогов.

        :param ldap_server: объект сервера службы каталогов
        :param user: объект пользователя
        :param account_name: имя пользовательской учетной записи
        :return: результат назначения системной группы пользователю службы каталогов
        """
        Log.debug(_('Assigning veil groups to {}').format(user.username))

        # Удаляем пользователя из всех групп.
        await user.remove_roles()
        await user.remove_groups()

        user_info, user_groups = self._get_ad_user_attributes(account_name,
                                                              self.domain_name,
                                                              ldap_server)

        # Если отображения отсутствуют, то по-умолчанию всем пользователям
        # назначается группа Оператор.
        mappings = await self.mappings
        Log.debug(_('Mappings: {}').format(mappings))

        if not mappings:
            await user.add_role(Role.VM_OPERATOR, creator='system')
            Log.debug(_('Role VM_OPERATOR has assigned to user {}.').format(user.username))
            return True

        user_veil_groups = False
        ad_ou, ad_groups = (get_ad_user_ou(user_info),
                            get_ad_user_groups(user_groups.get('memberOf', [])))

        # Производим проверку в порядке уменьшения приоритета.
        # В случае, если совпадение найдено,
        # проверка отображений более низкого приоритета не производится.

        # Если есть мэппинги, значит в системе есть группы. Поэтому тут производим пользователю назначение групп.
        for role_mapping in mappings:
            escaped_values = list(map(ldap.dn.escape_dn_chars, role_mapping.values))
            Log.debug(_('escaped values: {}').format(escaped_values))
            Log.debug(_('role mapping value type: {}').format(role_mapping.value_type))

            if role_mapping.value_type == Mapping.ValueTypes.USER:
                user_veil_groups = account_name in escaped_values
            elif role_mapping.value_type == Mapping.ValueTypes.OU:
                user_veil_groups = ad_ou in escaped_values
            elif role_mapping.value_type == Mapping.ValueTypes.GROUP:
                user_veil_groups = any([gr_name in escaped_values for gr_name in ad_groups])

            Log.debug(_('{}').format(role_mapping.value_type == Mapping.ValueTypes.GROUP))
            Log.debug(_('User veil groups: {}').format(user_veil_groups))
            if user_veil_groups:
                for group in await role_mapping.assigned_groups:
                    Log.debug(_('Attaching user {} to group: {}').format(user.username, group.verbose_name))
                    await group.add_user(user.id, creator='system')
                return True
        return False

    @classmethod
    async def get_domain_name(cls, username: str):
        """Возввращает доменное имя для контроллера AD.
           Если в username есть доменное имя - вернется оно, если нет - domain_name из записи AD."""
        _, domain_name = extract_domain_from_username(username)
        if not domain_name:
            authentication_directory = await AuthenticationDirectory.get_objects(first=True)
            if not authentication_directory:
                raise ValidationError(_('No authentication directory controllers.'))
            domain_name = authentication_directory.domain_name
        return domain_name

    @classmethod
    async def authenticate(cls, username, password):
        """
        Метод аутентификации пользователя на основе данных из службы каталогов.
        """
        authentication_directory = await AuthenticationDirectory.get_objects(first=True)
        if not authentication_directory:
            # Если для доменного имени службы каталогов не создано записей в БД,
            # то авторизоваться невозможно.
            raise ValidationError(_('No authentication directory controllers.'))

        account_name, domain_name = extract_domain_from_username(username)
        user, created = await cls._get_user(account_name)

        if not domain_name:
            domain_name = authentication_directory.domain_name
            username = '@'.join([username, domain_name])

        try:
            # TODO: заменить на self.connection
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            ldap_server = ldap.initialize(authentication_directory.directory_url)
            ldap_server.set_option(ldap.OPT_REFERRALS, 0)
            ldap_server.set_option(ldap.OPT_NETWORK_TIMEOUT, LDAP_TIMEOUT)
            ldap_server.simple_bind_s(username, password)

            await authentication_directory.assign_veil_roles(ldap_server, user, account_name)
            success = True
        except ldap.INVALID_CREDENTIALS as ldap_error:
            # Если пользователь не проходит аутентификацию в службе каталогов с предоставленными
            # данными, то аутентификация в системе считается неуспешной и создается событие с
            # сообщением о неуспешности.
            success = False
            created = False
            # Log.debug(ldap_error)
            raise ValidationError(_('Invalid credentials (ldap): {}').format(ldap_error))
        except ldap.SERVER_DOWN:
            # Если нет связи с сервером службы каталогов, то возвращаем ошибку о недоступности
            # сервера, так как не можем сделать вывод о правильности предоставленных данных.
            # self.server_down = True
            success = False
            created = False
            raise ValidationError(_('Server down (ldap).'))
        except Exception as E:
            Log.debug(E)
        finally:
            if not success and created:
                await user.delete()
        return account_name

    async def get_connection(self, username: str = None, password: str = None):
        """Соединение с AuthenticationDirectory для дальнейшей работы."""
        try:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            ldap_connection = ldap.initialize(self.directory_url)
            ldap_connection.set_option(ldap.OPT_REFERRALS, 0)
            ldap_connection.set_option(ldap.OPT_NETWORK_TIMEOUT, LDAP_TIMEOUT)
            # Данные авторизации для подключения
            decrypted_password = decrypt(self.service_password)
            full_username = '@'.join([self.service_username, self.domain_name])
            # Устанавливаем соединение, которое нужно не забыть закрыть
            # TODO: сделать менеджер контекста, чтобы соединения закрывались
            ldap_connection.simple_bind_s(full_username, decrypted_password)
        except (ldap.INVALID_CREDENTIALS, TypeError):
            msg = _('Authentication directory server {} has bad auth info.').format(self.directory_url)
            await Log.warning(msg, entity_dict=self.entity)
            await self.update(status=Status.BAD_AUTH).apply()
            return False
        except ldap.SERVER_DOWN:
            msg = _('Authentication directory server {} is down.').format(self.directory_url)
            await Log.warning(msg, entity_dict=self.entity)
            await self.update(status=Status.FAILED).apply()
            return False
        else:
            if self.status != Status.ACTIVE:
                await self.update(status=Status.ACTIVE).apply()
        return ldap_connection

    @property
    async def assigned_ad_groups(self):
        """Список групп у которых не пустое поле Group.ad_guid."""
        query = Group.query.where(Group.ad_guid.isnot(None))
        return await query.gino.all()

    async def build_group_filter(self):
        """Строим фильтр для поиска групп в Authentication Directory."""
        base_filter = '(&(objectCategory=GROUP)(groupType=-2147483646)(!(isCriticalSystemObject=TRUE))'
        # Список групп у которых есть признак синхронизации
        assigned_groups = await self.assigned_ad_groups
        # Строим фильтр исключающий группы по Guid
        groups_filter = ['(!(objectGUID={}))'.format(pack_guid(group.ad_guid)) for group in assigned_groups]
        # Добавляем фильтр к существующему
        groups_filter.insert(0, base_filter)
        # Строим итоговый фильтр
        final_filter = ''.join(groups_filter) + ')'
        return final_filter

    async def get_possible_ad_groups(self):
        """Список групп хранящихся в AuthenticationDirectory за вычетом синхронизированных."""
        # TODO: Искать по groupName, если поиск по GUID ничего не дал?
        connection = await self.get_connection()
        if not connection:
            return list()
        try:
            dc_filter = 'dc={},dc={}'.format(*self.domain_name.split('.'))
            groups_filter = await self.build_group_filter()
            # groups: [('CN=Users, DC=team', {'objectGUID': [b'~\xecIO\xa3\x88vE\xbb0\x86\xfe\xa0\x0fA+']}), ]
            groups = connection.search_s(dc_filter, ldap.SCOPE_SUBTREE, groups_filter)

            groups_list = list()
            for group in groups:
                ad_search_cn = group[0]
                # Если не указан ad_search_cn - не получится найти членов группы
                if not ad_search_cn:
                    continue
                # Получаем dict с информацией о группе
                ad_group_info = group[1]
                # Наименование группы AuthenticationDirectory
                cn = unpack_ad_info(ad_group_info, self.AD_GROUP_NAME)
                # Уникальный идентификатор объекта AuthenticationDirectory
                object_guid = unpack_ad_info(ad_group_info, self.AD_GROUP_ID)
                # cn это обычная bytes-строка
                if cn:
                    cn = cn.decode('utf-8')
                # GUID используется из-за проблем конвертации Sid и минимальной версии 2012+
                if object_guid:
                    object_guid = unpack_guid(object_guid)
                # Нужно оба параметра
                if object_guid and cn:
                    groups_list.append({'ad_guid': object_guid, 'verbose_name': cn, 'ad_search_cn': ad_search_cn})
        except ldap.LDAPError:
            # На случай ошибочности запроса к AD
            msg = _('Fail to connect to Authentication Directory. Check service information')
            await Log.error(msg)
            await self.update(status=Status.FAILED).apply()
            groups_list = list()
        connection.unbind_s()
        return groups_list

    @staticmethod
    def build_group_user_filter(groups_cn: list):
        """Строим фильтр для поиска пользователей членов групп в Authentication Directory."""
        base_filter = '(&(sAMAccountName=*)'
        locked_account_filter = '(!(userAccountControl:1.2.840.113556.1.4.803:=2))'
        persons_filter = '(|(objectCategory=USER)(objectCategory=PERSON))(objectClass=USER)'
        member_of_filter = '(memberOf={})'.format(groups_cn)

        # На случай если захотят много групп
        # member_of_pattern = '(memberOf={})'
        #
        # # Добавляем через ИЛИ группы для вхождения
        # member_filter_list = [member_of_pattern.replace('{}', group_cn) for group_cn in groups_cn]
        # if member_filter_list and isinstance(member_filter_list, list):
        #     member_filter_list.insert(0, '(!')
        #     member_filter_list.append(')')
        # member_of_filter = ''.join(member_filter_list)

        # Строим итоговый фильтр
        final_filter = ''.join([base_filter, locked_account_filter, persons_filter, member_of_filter, ')'])
        return final_filter

    async def get_members_of_ad_group(self, group_cn: str):
        """Пользователи члены группы в Authentication Directory."""
        connection = await self.get_connection()
        if not connection:
            return list()
        try:
            dc_filter = 'dc={},dc={}'.format(*self.domain_name.split('.'))
            users_filter = self.build_group_user_filter(group_cn)
            users = connection.search_s(dc_filter, ldap.SCOPE_SUBTREE, users_filter)

            # Парсим ответ от Authentication Directory
            users_list = list()
            for user in users:
                ad_search_cn = user[0]
                # Если не указан ad_search_cn - не получится получить информацию о пользователе
                if not ad_search_cn:
                    continue
                # Получаем dict с информацией о пользователе
                ad_user_info = user[1]
                # Наименование группы AuthenticationDirectory
                username = unpack_ad_info(ad_user_info, self.AD_USERNAME)
                email = unpack_ad_info(ad_user_info, self.AD_EMAIL)
                fullname = unpack_ad_info(ad_user_info, self.AD_FULLNAME)
                first_name = unpack_ad_info(ad_user_info, self.AD_FIRST_NAME)
                last_name = unpack_ad_info(ad_user_info, self.AD_SURNAME)

                # Преобразуем bytes-строки
                username = username.decode('utf-8') if username else None
                email = email.decode('utf-8') if email else None
                fullname = fullname.decode('utf-8') if fullname else None
                first_name = first_name.decode('utf-8') if first_name else None
                last_name = last_name.decode('utf-8') if last_name else None

                # Если не указано имя и фамилия - пытаемся разобрать fullname
                if (not first_name or not last_name) and fullname:
                    first_name, *last_name = fullname.split()
                    if isinstance(last_name, list):
                        last_name = ' '.join(last_name)

                # Перепроверяем чтобы при пустой строке был None
                last_name = last_name if last_name else None
                first_name = first_name if first_name else None

                # Нужен как минимум username
                if username:
                    users_list.append({'username': username,
                                       'email': email,
                                       'first_name': first_name,
                                       'last_name': last_name})
        except ldap.LDAPError:
            msg = _('Fail to connect to Authentication Directory. Check service information')
            await Log.error(msg)
            await self.update(status=Status.FAILED).apply()
            users_list = list()
        connection.unbind_s()
        return users_list

    @staticmethod
    async def sync_group(group_info):
        """При необходимости создает группу из Authentication Directory на VDI."""
        group = await Group.query.where(Group.verbose_name == group_info['verbose_name']).gino.first()
        if group:
            await group.update(ad_guid=str(group_info['ad_guid'])).apply()
            return group
        try:
            group = await Group.soft_create(creator='system', **group_info)
        except UniqueViolationError:
            # Если срабатывает этот сценарий - что-то пошло не поплану
            return await Group.query.where(Group.ad_guid == str(group_info['ad_guid'])).gino.first()
        return group

    @staticmethod
    async def sync_users(users_info):
        """При необходимости создает пользователей из Authentication Directory на VDI."""
        users_list = list()
        async with db.transaction():
            for user_info in users_info:
                username = user_info['username']
                last_name = user_info.get('last_name')
                first_name = user_info.get('first_name')
                email = user_info.get('email')
                # Ищем пользователя в системе
                user = await User.query.where(User.username == username).gino.first()
                if user:
                    users_list.append(user.id)
                    continue
                # Создаем пользователя
                user = await User.soft_create(username=username, last_name=last_name, first_name=first_name,
                                              email=email, creator='system')
                if user:
                    users_list.append(user.id)
        return users_list

    async def synchronize(self, data):
        """Синхронизирует переданные группы и пользователи из Authentication Directory на VDI."""
        # Создаем группу
        group_info = {
            'ad_guid': data['group_ad_guid'],
            'verbose_name': data['group_verbose_name']
        }
        group = await self.sync_group(group_info)
        # Создаем пользователей
        users_info = data.get('group_members')
        if users_info and isinstance(users_info, list):
            users_list = await self.sync_users(users_info)
        else:
            users_list = None
        # Включаем пользователей в группу
        if users_list:
            await group.add_users(users_list, creator='system')
        return True


class Mapping(AbstractClass):
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
