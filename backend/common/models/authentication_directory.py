# -*- coding: utf-8 -*-
import uuid
from collections.abc import Iterable
from enum import Enum
from typing import Optional, Tuple

from asyncpg.exceptions import UniqueViolationError

import ldap
from ldap.controls.libldap import SimplePagedResultsControl as LdapPageCtrl

from sqlalchemy import Enum as AlchemyEnum, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import desc, text

from common.database import db
from common.languages import _local_
from common.log.journal import system_logger
from common.models.auth import Group as GroupModel, User as UserModel
from common.settings import (LDAP_LOGIN_PATTERN,
                             LDAP_NETWORK_TIMEOUT,
                             LDAP_OPT_REFERRALS,
                             LDAP_TIMEOUT,
                             OPENLDAP_LOGIN_PATTERN)
from common.veil.auth.auth_dir_utils import (
    extract_domain_from_username,
    get_ad_user_ou,
    get_free_ipa_user_groups,
    get_free_ipa_user_ou,
    get_ms_ad_user_groups,
    pack_guid,
    unpack_ad_info,
    unpack_guid
)
from common.veil.auth.fernet_crypto import decrypt, encrypt
from common.veil.veil_errors import SilentError, ValidationError
from common.veil.veil_gino import (
    AbstractSortableStatusModel,
    EntityType,
    Status,
    VeilModel,
)

PAGE_SIZE = 999


# На время работы search_ext_s, result3 текщий процесс не будет отвечать на запросы.
# По-хорошему нужен асинхронный аналог модуля для работы с ldap. Но так как добавление AD -
# это очень редкая операция, то мб и так сойдет.

class AuthenticationDirectory(VeilModel, AbstractSortableStatusModel):
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

    class ConnectionTypes(Enum):
        """Доступные типы подключения служб каталогов."""

        LDAP = "LDAP"

    class DirectoryTypes(Enum):
        """Доступные типы служб каталогов."""

        ActiveDirectory = "ActiveDirectory"
        FreeIPA = "FreeIPA"
        OpenLDAP = "OpenLDAP"
        ALD = "ALD"

    AD_GROUP_ID = "objectGUID"
    IPA_GROUP_ID = "ipaUniqueID"
    AD_GROUP_NAME = "cn"
    AD_USERNAME = "sAMAccountName"
    IPA_USERNAME = "uid"
    AD_EMAIL = "mail"
    AD_FULLNAME = "displayName"
    AD_FIRST_NAME = "givenName"
    AD_SURNAME = "sn"

    __tablename__ = "authentication_directory"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=255), unique=True)
    connection_type = db.Column(
        AlchemyEnum(ConnectionTypes),
        nullable=False,
        server_default=ConnectionTypes.LDAP.value,
    )
    description = db.Column(db.Unicode(length=255), nullable=True)
    directory_url = db.Column(db.Unicode(length=255))
    directory_type = db.Column(
        AlchemyEnum(DirectoryTypes),
        nullable=False,
        server_default=DirectoryTypes.ActiveDirectory.value,
    )
    domain_name = db.Column(db.Unicode(length=255), unique=True)
    dc_str = db.Column(db.Unicode(length=255), unique=True)
    service_username = db.Column(db.Unicode(length=150), nullable=True)
    # Из-за шифрования размер строки с паролем сильно увеличивается.
    service_password = db.Column(db.Unicode(length=1000), nullable=True)
    status = db.Column(AlchemyEnum(Status), nullable=False, index=True)

    @property
    def entity_type(self):
        return EntityType.AUTH

    @property
    def entity(self):
        return {"entity_type": self.entity_type, "entity_uuid": self.id}

    @property
    def mappings_query(self):
        return (
            Mapping.join(
                GroupAuthenticationDirectoryMapping.query.where(
                    AuthenticationDirectory.id == self.id
                ).alias()
            )
            .select()
            .order_by(desc(Mapping.priority))
        )

    @property
    async def mappings(self):
        return await self.mappings_query.gino.load(Mapping).all()

    @property
    def password(self):
        """Дешифрованный пароль."""
        return decrypt(self.service_password)

    @property
    def connection_username(self):
        """Логин с доменом."""
        if self.directory_type == AuthenticationDirectory.DirectoryTypes.FreeIPA:
            return LDAP_LOGIN_PATTERN.format(
                username=self.service_username, dc=self.convert_dc_str(self.dc_str))
        elif self.directory_type == AuthenticationDirectory.DirectoryTypes.OpenLDAP:
            return OPENLDAP_LOGIN_PATTERN.format(
                username=self.service_username, dc=self.convert_dc_str(self.dc_str))
        return (
            "\\".join([self.domain_name, self.service_username])
            if self.service_username and self.domain_name
            else False
        )

    async def mappings_paginator(self, limit, offset):
        return (
            await self.mappings_query.limit(limit)
            .offset(offset)
            .gino.load(Mapping)
            .all()
        )

    @classmethod
    async def soft_create(
        cls,
        verbose_name,
        directory_url,
        domain_name: str,
        creator,
        dc_str: str,
        service_username=None,
        service_password=None,
        description=None,
        connection_type=ConnectionTypes.LDAP,
        directory_type=DirectoryTypes.ActiveDirectory,
        id=None,
    ):
        """Создает запись Authentication Directory.

        Если не удалось проверить соединение - статус изменится на Failed.
        """
        # Ограничение на количество записей
        count = await db.func.count(AuthenticationDirectory.id).gino.scalar()
        if count > 0:
            raise SilentError(
                _local_("More than one authentication directory can not be created.")
            )
        # Шифруем пароль
        if service_password and isinstance(service_password, str):
            service_password = encrypt(service_password)

        auth_dir_dict = {
            "verbose_name": verbose_name,
            "description": description,
            "directory_url": directory_url,
            "connection_type": connection_type,
            "directory_type": directory_type,
            "domain_name": domain_name.upper(),
            "service_username": service_username,
            "service_password": service_password,
            "status": Status.CREATING,
            "dc_str": dc_str,
        }
        if id:
            auth_dir_dict["id"] = id
        # Создаем запись
        auth_dir = await AuthenticationDirectory.create(**auth_dir_dict)
        await system_logger.info(
            _local_("Authentication directory {} is created.").format(
                auth_dir_dict.get("verbose_name")
            ),
            user=creator,
            entity=auth_dir.entity,
        )
        # Проверяем доступность
        await auth_dir.test_connection()
        return auth_dir

    @staticmethod
    def convert_dc_str(dc_by_dot: str):
        """Если запись формата bazalt.team, то будет конвертировано на dc=bazalt, dc=team."""
        if dc_by_dot and isinstance(dc_by_dot, str):
            dc_l = dc_by_dot.split(".")
            if len(dc_l) > 1:
                return ",".join(["dc={}".format(dc) for dc in dc_l])
        return dc_by_dot

    @classmethod
    async def soft_update(cls, id, **kwargs):

        if kwargs and isinstance(kwargs, dict):
            if kwargs.get("service_password"):
                kwargs["service_password"] = encrypt(kwargs["service_password"])
            # Переводим NetBIOS имя домена в верхний регистр
            domain_name = kwargs.get("domain_name")
            if domain_name and isinstance(domain_name, str):
                kwargs["domain_name"] = domain_name.upper()

        update_type, update_dict = await super().soft_update(id, **kwargs)

        creator = update_dict.pop("creator")
        desc = str(update_dict)
        await system_logger.info(
            _local_("Values for auth directory is updated."),
            entity=update_type.entity,
            description=desc,
            user=creator,
        )

        await update_type.test_connection()
        return update_type

    async def soft_delete(self, creator):
        parent = super().soft_delete(creator)

        # Удаляем у существующих групп все ad_guid
        await GroupModel.update.values(ad_guid=None).where(
            GroupModel.ad_guid.isnot(None)
        ).gino.status()
        # Удаляем все мэппинги
        await Mapping.delete.gino.status()
        return parent

    async def add_mapping(self, mapping: dict, groups: list, creator):
        """
        :param mapping: Dictionary of Mapping table kwargs.

        :param groups: List of GroupModel.id strings.
        """
        async with db.transaction():
            mapping_obj = await Mapping.create(**mapping)
            for group_id in groups:
                await GroupAuthenticationDirectoryMapping.create(
                    authentication_directory_id=self.id,
                    group_id=group_id,
                    mapping_id=mapping_obj.id,
                )
                group_name = await GroupModel.get(group_id)
                desc = _local_("Arguments: {} of group: {}.").format(
                    mapping, group_name.verbose_name
                )
                msg = _local_("Mapping for auth directory {} is created.").format(
                    self.verbose_name
                )
                await system_logger.info(
                    msg, entity=mapping_obj.entity, description=desc, user=creator
                )

    async def edit_mapping(self, mapping: dict, groups: list, creator):
        """
        :param mapping: Dictionary of Mapping table kwargs.

        :param groups: List of GroupModel.id strings.
        """
        async with db.transaction():
            mapping_id = mapping.pop("mapping_id")
            mapping_obj = await Mapping.get(mapping_id)
            await mapping_obj.soft_update(
                mapping_id,
                verbose_name=mapping.get("verbose_name"),
                description=mapping.get("description"),
                value_type=mapping.get("value_type"),
                values=mapping.get("values"),
                priority=mapping.get("priority"),
                creator=creator,
            )
            if groups:
                await GroupAuthenticationDirectoryMapping.delete.where(
                    GroupAuthenticationDirectoryMapping.mapping_id == mapping_id
                ).gino.status()
                for group_id in groups:
                    await GroupAuthenticationDirectoryMapping.create(
                        authentication_directory_id=self.id,
                        group_id=group_id,
                        mapping_id=mapping_id,
                    )
                    group_name = await GroupModel.get(group_id)
                    desc = _local_("New arguments: {} of group: {}.").format(
                        mapping, group_name.verbose_name
                    )
                    msg = _local_("Mapping for auth directory {} is updated.").format(
                        self.verbose_name
                    )
                    await system_logger.info(
                        msg, entity=self.entity, description=desc, user=creator
                    )

    async def test_connection(self) -> bool:
        """Метод тестирования соединения с сервером службы каталогов.

        :return: результат проверки соединения
        """
        try:
            ldap_server = ldap.initialize(self.directory_url)
            ldap_server.set_option(ldap.OPT_TIMEOUT, LDAP_TIMEOUT)
            ldap_server.set_option(ldap.OPT_NETWORK_TIMEOUT, LDAP_NETWORK_TIMEOUT)
            # additional connection options
            ldap_server.set_option(ldap.OPT_REFERRALS, LDAP_OPT_REFERRALS)
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

            # Если у записи есть данные auth - проверяем их
            if self.service_password and self.service_username:
                ldap_server.simple_bind_s(self.connection_username, self.password)
            else:
                ldap_server.simple_bind_s()
        except (ldap.INVALID_CREDENTIALS, TypeError):
            await self.update(status=Status.BAD_AUTH).apply()
            return False
        except ldap.SERVER_DOWN as ex_error:
            msg = _local_("Authentication directory server {} is down.").format(
                self.directory_url
            )
            await system_logger.warning(msg, entity=self.entity, description=ex_error)
            await self.update(status=Status.FAILED).apply()
            return False
        else:
            ldap_server.unbind_s()
            await self.update(status=Status.ACTIVE).apply()
        await system_logger.info(
            _local_("Authentication directory server {} is connected.").format(
                self.directory_url
            ),
            entity=self.entity,
        )
        return True

    # Authentication Directory synchronization methods

    async def sync_openldap_users(self, ou, creator="system"):
        if self.directory_type == AuthenticationDirectory.DirectoryTypes.OpenLDAP:
            ldap_server = ldap.initialize(self.directory_url)
            dc_str = self.convert_dc_str(self.dc_str)
            openldap_users = ldap_server.search_s("ou={},{}".format(ou, dc_str), ldap.SCOPE_SUBTREE)
            sync_members = list()
            for user in openldap_users:
                if user[1].get("ou"):
                    continue
                info = dict()
                info["first_name"] = user[1].get("givenName")[0].decode("UTF-8") if user[1].get("givenName") else user[1].get("givenName")
                info["username"] = user[1].get("cn")[0].decode("UTF-8") if user[1].get("cn") else user[1].get("cn")
                info["last_name"] = user[1].get("sn")[0].decode("UTF-8") if user[1].get("sn") else user[1].get("sn")
                info["email"] = user[1].get("mail")[0].decode("UTF-8") if user[1].get("mail") else user[1].get("mail")
                sync_members.append(info)
            # group = await GroupModel.soft_create(verbose_name="OpenLDAP", creator="system")
            await self.sync_users(sync_members, creator=creator)
            # new_users = await self.sync_users(sync_members)
            # await group.add_users(user_id_list=new_users, creator="system")
            return True
        raise SilentError("Not OpenLDAP directory.")

    async def get_ad_user_attributes(
        self, ldap_server: "ldap.ldapobject.SimpleLDAPObject", account_name: str, domain_name: str
    ) -> Tuple[Optional[str], dict]:
        """Получение информации о текущем пользователе из службы каталогов.

        :param account_name: имя пользовательской учетной записи
        :param domain_name: имя домена для авторизующегося пользователя
        :param ldap_server: объект сервера службы каталогов
        :return: атрибуты пользователя службы каталогов
        """
        # # Расширено 31.05.2021
        # # формируем запрос для AD
        # dc_str = self.convert_dc_str(self.dc_str)
        # if self.directory_type == self.DirectoryTypes.FreeIPA:
        #     base = LDAP_LOGIN_PATTERN.format(username=account_name, dc=dc_str)
        #     user_info_filter = "(objectClass=person)"
        # else:
        #     base = dc_str
        #     user_info_filter = "(&(objectClass=user)(sAMAccountName={}))".format(
        #         account_name
        #     )
        # # получаем данные пользователя из AD
        # req_ctrl = LdapPageCtrl(criticality=True, size=PAGE_SIZE, cookie="")
        # user_info, user_groups = ldap_server.search_ext_s(
        #     base=base, scope=ldap.SCOPE_SUBTREE, filterstr=user_info_filter,
        #     attrlist=["memberOf"], serverctrls=[req_ctrl]
        # )[0]

        # Расширено 10.11.2021 (взято из ECP)
        base = self.convert_dc_str(domain_name)
        if (self.directory_type == AuthenticationDirectory.DirectoryTypes.FreeIPA) or (
            self.directory_type == AuthenticationDirectory.DirectoryTypes.OpenLDAP):  # noqa E125
            user_info_filter = "(uid={})".format(account_name)
        else:
            user_info_filter = "(&(objectClass=user)(sAMAccountName={}))".format(account_name)
        user_data = ldap_server.search_s(base=base,
                                         scope=ldap.SCOPE_SUBTREE,
                                         filterstr=user_info_filter,
                                         attrlist=["memberOf"])
        if user_data and isinstance(user_data, list):
            user_info, user_groups = user_data[0]
            return user_info, user_groups
        return "", {}

    @classmethod
    async def _get_user(cls, username: str):
        """Получение объекта пользователя из БД на основе его имени.

        Если пользователь не существует, то будет создан с пустым паролем.
        Авторизация этого пользователя возможна только по LDAP.

        :param username: имя пользователя
        :return: объект пользователя, флаг создания пользователя
        """
        if not isinstance(username, str):
            raise ValidationError(_local_("Username must be a string."))

        # username = username.lower()
        user = await UserModel.get_object(
            extra_field_name="username",
            extra_field_value=username,
            include_inactive=True,
        )
        if not user:
            # user = await UserModel.soft_create(username, by_ad=True, local_password=False, creator="system")
            # created = True
            users_list = await UserModel.get_object(
                extra_field_name="username",
                extra_field_value=username,
                include_inactive=True,
                similar=True
            )
            users = ", ".join([user.username for user in users_list]) if users_list else _local_("something other.")
            raise SilentError(_local_("Username {} is incorrect. Maybe you mean {}.").format(username, users))
        else:
            # await user.update(is_active=True).apply()
            if not user.is_active:
                raise SilentError(_local_("User {} is deactivate.").format(username))
            created = False
        return user, created

    @staticmethod
    async def init_ldap(ad, directory_url: str = None):
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        ldap_connection = ldap.initialize(directory_url or ad.directory_url)
        ldap_connection.set_option(ldap.OPT_REFERRALS, 0)
        ldap_connection.set_option(ldap.OPT_NETWORK_TIMEOUT, LDAP_TIMEOUT)
        if ad.directory_type == AuthenticationDirectory.DirectoryTypes.ActiveDirectory and not directory_url:
            ldap_connection.simple_bind_s(ad.connection_username, ad.password)
        return ldap_connection

    async def assign_veil_roles(
        self,
        user: "UserModel",
        account_name: str,
        user_info: str,
        user_groups: dict
    ) -> bool:
        """
        Метод назначения пользователю системной группы на основе атрибутов его учетной записи в службе каталогов.

        :param user: объект пользователя
        :param account_name: имя пользовательской учетной записи
        :param user_info: dn пользователя ldap
        :param user_groups: информация о группах пользователя
        :return: результат назначения системной группы пользователю службы каталогов
        """
        mappings = await self.mappings
        await system_logger.debug(_local_("Mappings: {}.").format(mappings))

        if not mappings:
            return True

        user_veil_groups = False
        # Расширено 31.05.2021
        if self.directory_type == self.DirectoryTypes.FreeIPA:
            ad_ou = get_free_ipa_user_ou(user_info)
            ad_groups = get_free_ipa_user_groups(user_groups.get("memberOf", []))
        else:
            ad_ou = get_ad_user_ou(user_info)
            ad_groups = get_ms_ad_user_groups(user_groups.get("memberOf", []))

        # Производим проверку в порядке уменьшения приоритета.
        # В случае, если совпадение найдено,
        # проверка отображений более низкого приоритета не производится.

        # Если есть сопоставления, значит в системе есть группы.
        # Поэтому тут производим пользователю назначение групп.

        for role_mapping in mappings:
            escaped_values = list(map(ldap.dn.escape_dn_chars, role_mapping.values))
            await system_logger.debug(
                _local_("escaped values: {}.").format(escaped_values))
            await system_logger.debug(
                _local_("role mapping value type: {}.").format(role_mapping.value_type)
            )

            if role_mapping.value_type == Mapping.ValueTypes.USER:
                user_veil_groups = account_name in escaped_values
            elif role_mapping.value_type == Mapping.ValueTypes.OU:
                user_veil_groups = ad_ou in escaped_values
            elif role_mapping.value_type == Mapping.ValueTypes.GROUP:
                user_veil_groups = any(
                    [gr_name in escaped_values for gr_name in ad_groups]
                )

            await system_logger.debug(
                _local_("User VeiL groups: {}.").format(user_veil_groups)
            )

            if user_veil_groups:
                for group in await role_mapping.assigned_groups:
                    user_groups = await user.assigned_groups_ids
                    if group.id not in user_groups:
                        await system_logger.debug(
                            _local_("Attaching user {} to group: {}.").format(
                                user.username, group.verbose_name
                            )
                        )
                        await group.add_user(user.id, creator="system")
                return True
        return False

    @classmethod
    async def get_domain_name(cls, username: str):
        """Возвращает доменное имя для контроллера AD.

        Если в username есть доменное имя - вернется оно, если нет - domain_name из записи AD.
        """
        _, domain_name = extract_domain_from_username(username)
        if not domain_name:
            authentication_directory = await AuthenticationDirectory.get_objects(
                first=True
            )
            if not authentication_directory:
                raise ValidationError(
                    _local_("No authentication directory controllers."))
            domain_name = authentication_directory.dc_str
        return domain_name

    @classmethod
    async def authenticate(cls, username, password):
        """Метод аутентификации пользователя на основе данных из службы каталогов."""
        authentication_directory = await AuthenticationDirectory.get_objects(first=True)
        if not authentication_directory:
            # Если для доменного имени службы каталогов не создано записей в БД,
            # то авторизоваться невозможно.
            raise ValidationError(_local_("No authentication directory controllers."))

        account_name, domain_name = extract_domain_from_username(username)
        if domain_name == authentication_directory.dc_str or not domain_name:
            user, created = await cls._get_user(account_name)
        dc_str = cls.convert_dc_str(authentication_directory.dc_str)
        # Добавлено 31.05.2021
        if authentication_directory.directory_type == AuthenticationDirectory.DirectoryTypes.FreeIPA:
            username = LDAP_LOGIN_PATTERN.format(
                username=username, dc=dc_str)
            if not domain_name:
                domain_name = dc_str
        elif authentication_directory.directory_type == AuthenticationDirectory.DirectoryTypes.ActiveDirectory:
            if not domain_name:
                domain_name = authentication_directory.dc_str
                username = "@".join([account_name, domain_name])
                # domain_name = authentication_directory.domain_name
                # username = "\\".join([domain_name, account_name])
        try:
            ldap_server = await cls.init_ldap(authentication_directory)
            user_dn, user_groups = await authentication_directory.get_ad_user_attributes(ldap_server,
                                                                                         account_name,
                                                                                         domain_name)
            if authentication_directory.directory_type == AuthenticationDirectory.DirectoryTypes.ActiveDirectory:
                ldap_server.simple_bind_s(username, password)
            else:
                if not user_dn:
                    raise ValidationError(_local_("Invalid credentials."))
                ldap_server.simple_bind_s(user_dn, password)
            user = await UserModel.get_object(
                extra_field_name="username",
                extra_field_value=account_name,
                include_inactive=True,
            )
            await authentication_directory.assign_veil_roles(
                user, account_name, user_dn, user_groups
            )
            created = False
            success = True
        except ldap.INVALID_CREDENTIALS as ldap_error:
            # Если пользователь не проходит ауф в службе с предоставленными
            # данными, то ауф в системе считается неуспешной и создается событие
            # о провале.
            success = False
            raise ValidationError(
                _local_("Invalid credentials (ldap): {}.").format(ldap_error)
            )
        except ldap.SERVER_DOWN:
            # Если нет связи с сервером службы каталогов,
            # то возвращаем ошибку о недоступности сервера
            success = False
            raise ValidationError(_local_("Server down (ldap)."))
        except ldap.REFERRAL as e:
            ref_url, referral_dn = await cls._get_ldap_referral_dn(e)
            if not referral_dn:
                raise ValidationError(_local_(
                    "The LDAP server provides an alternate address to which an LDAP request can be processed, but the attempt was unsuccessful."))
            try:
                ldap_server = await cls.init_ldap(authentication_directory, ref_url)
                ldap_server.simple_bind_s(username, password)
                user_dn, user_groups = await authentication_directory.get_ad_user_attributes(ldap_server,
                                                                                             account_name,
                                                                                             domain_name)
                user = await UserModel.get_object(
                    extra_field_name="username",
                    extra_field_value=username,
                    include_inactive=True,
                )
                if not user:
                    user = await UserModel.soft_create(username, by_ad=True, local_password=False, creator="system")
                    created = True
                await authentication_directory.assign_veil_roles(
                    user, account_name, user_dn, user_groups
                )
                success = True
                return username
            except ldap.INVALID_CREDENTIALS as ldap_error:
                # Если пользователь не проходит ауф в службе с предоставленными
                # данными, то ауф в системе считается неуспешной и создается событие
                # о провале.
                success = False
                raise ValidationError(
                    _local_("Invalid credentials (ldap): {}.").format(ldap_error)
                )
            except ldap.SERVER_DOWN:
                # Если нет связи с сервером службы каталогов,
                # то возвращаем ошибку о недоступности сервера
                success = False
                raise ValidationError(_local_("Server down (ldap)."))
        except Exception as E:
            success = False
            await system_logger.debug(E)
            raise ValidationError("LDAP Error: {}".format(str(E)))
        finally:
            try:
                if not success and created:
                    await user.delete()
            except:  # noqa
                pass
        return account_name

    @staticmethod
    async def _get_ldap_referral_dn(referral_exception) -> tuple:
        """Заготовка для обработки referral ссылок."""
        if not referral_exception.args[0] or not referral_exception.args[0].get("info"):
            await system_logger.debug("LDAP referral missing 'info' block.")
            return None, None
        referral_info = referral_exception.args[0]["info"]
        if not referral_info.startswith("Referral:\n"):
            await system_logger.debug("LDAP referral missing 'Referral' header.")
            return None, None
        referral_uri = referral_info[len("Referral:\n"):]
        if not referral_uri.startswith("ldap"):
            await system_logger.debug("LDAP referral URI does not start with 'ldap'.")
            return None, None
        if referral_uri.startswith("ldap://"):
            ldap_protocol = "ldap://"
        else:
            ldap_protocol = "ldaps://"
        if referral_uri.startswith("{}/".format(ldap_protocol)):
            referral_dn = referral_uri[len("{}/".format(ldap_protocol)):]
            ref_url = ".".join([dc[len("dc="):] for dc in referral_dn.split(",") if "dc=" in dc])
        else:
            ref_url, referral_dn = referral_uri[len(ldap_protocol):].split("/")
        return "{}{}".format(ldap_protocol, ref_url), referral_dn

    async def get_connection(self):
        """Соединение с AuthenticationDirectory для дальнейшей работы."""
        try:
            # Прерываем выполнение, если не указаны данные подключения
            if not self.service_username or not self.service_password:
                raise AssertionError(
                    _local_("LDAP username and password can`t be empty."))
            # Пытаемся подключиться
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            ldap_connection = ldap.initialize(self.directory_url)
            ldap_connection.set_option(ldap.OPT_REFERRALS, 0)
            ldap_connection.set_option(ldap.OPT_NETWORK_TIMEOUT, LDAP_TIMEOUT)
            ldap_connection.simple_bind_s(self.connection_username, self.password)
        except (ldap.INVALID_CREDENTIALS, TypeError):
            msg = _local_(
                "Authentication directory server {} has bad auth info.").format(
                self.directory_url
            )
            await system_logger.warning(msg, entity=self.entity)
            await self.update(status=Status.BAD_AUTH).apply()
            return False
        except ldap.SERVER_DOWN:
            msg = _local_("Authentication directory server {} is down.").format(
                self.directory_url
            )
            await system_logger.warning(msg, entity=self.entity)
            await self.update(status=Status.FAILED).apply()
            return False
        else:
            if self.status != Status.ACTIVE:
                await self.update(status=Status.ACTIVE).apply()
        return ldap_connection

    async def assigned_ad_groups(self, group_name=""):
        """Список групп у которых не пустое поле GroupModel.ad_guid."""
        query = GroupModel.query.order_by("verbose_name").where(GroupModel.ad_guid.isnot(None))
        if group_name:
            query = query.where(GroupModel.verbose_name.ilike("%{}%".format(group_name)))
        return await query.gino.all()

    async def build_group_filter(self, group_name=""):
        """Строим фильтр для поиска групп в Authentication Directory."""
        # Список групп у которых есть признак синхронизации
        assigned_groups = await self.assigned_ad_groups()

        # Фильтр для поиска групп
        if self.directory_type == self.DirectoryTypes.ActiveDirectory:
            system_groups = "(!(isCriticalSystemObject=TRUE))"
            base_filter = "(&(objectCategory=GROUP){}".format(system_groups)
            groups_filter = [
                "(!(objectGUID={}))".format(pack_guid(group.ad_guid))
                for group in assigned_groups
            ]
            groups_filter.append("(Name={}*)".format(group_name))  # wildcard * не хочет работать впереди
        elif self.directory_type == self.DirectoryTypes.FreeIPA:
            base_filter = "(&(objectclass=ipausergroup)(!(nsaccountlock=TRUE))"
            groups_filter = [
                "(!(ipaUniqueID={}))".format(group.ad_guid)
                for group in assigned_groups
            ]
            groups_filter.append("(cn={}*)".format(group_name))  # В случае IPA wildcard не работает с обеих сторон
        else:
            raise NotImplementedError(
                "{} not implemented yet.".format(self.directory_type))

        # Строим фильтр исключающий группы по Guid

        # Добавляем фильтр к существующему
        groups_filter.insert(0, base_filter)
        # Строим итоговый фильтр
        final_filter = "".join(groups_filter) + ")"
        return final_filter

    def extract_groups(self, ldap_response: Iterable) -> list:
        if self.directory_type == self.DirectoryTypes.ActiveDirectory:
            return self.extract_ms_ad_group(ldap_response)
        elif self.directory_type == self.DirectoryTypes.FreeIPA:
            return self.extract_free_ipa_group(ldap_response)
        raise NotImplementedError(
            "{} not implemented yet.".format(self.directory_type))

    def extract_ms_ad_group(self, ldap_response: Iterable) -> list:
        """Извлечь группы с идентификаторами из ответа MS AD."""
        groups = list()
        for group in ldap_response:
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
                cn = cn.decode("utf-8")
            # GUID используется из-за проблем конвертации Sid и минимальной версии 2012+
            if object_guid:
                object_guid = unpack_guid(object_guid)
            # Нужно оба параметра
            if object_guid and cn:
                groups.append(
                    {
                        "ad_guid": object_guid,
                        "verbose_name": cn,
                        "ad_search_cn": ad_search_cn,
                    }
                )
        return groups

    def extract_free_ipa_group(self, ldap_response: Iterable) -> list:
        """Извлечь группы с идентификаторами из ответа Free IPA."""
        groups = list()
        for group in ldap_response:
            ad_search_cn = group[0]
            # Если не указан ad_search_cn - не получится найти членов группы
            if not ad_search_cn:
                continue
            for attr in group:
                if isinstance(attr, dict):
                    cn = attr.get("cn", [""])[0]
                    ad_guid = attr.get(self.IPA_GROUP_ID, [""])[0]
                    cn = cn.decode("utf-8") if isinstance(cn, bytes) else cn
                    ad_guid = ad_guid.decode("utf-8") if isinstance(ad_guid,
                                                                    bytes) else ad_guid
                    if cn and ad_guid:
                        groups.append(
                            {
                                "ad_guid": ad_guid,
                                "verbose_name": cn,
                                "ad_search_cn": ad_search_cn,
                            }
                        )
                        break
        return groups

    async def get_possible_ad_groups(self, group_name="") -> list:
        """Список групп за вычетом уже синхронизированных."""
        connection = await self.get_connection()
        if not connection or self.directory_type == AuthenticationDirectory.DirectoryTypes.OpenLDAP:
            return list()
        try:
            req_ctrl = LdapPageCtrl(criticality=True, size=PAGE_SIZE, cookie="")
            groups_filter = await self.build_group_filter(group_name)
            dc_str = self.convert_dc_str(self.dc_str)
            ldap_groups = connection.search_ext_s(base=dc_str, scope=ldap.SCOPE_SUBTREE,
                                                  filterstr=groups_filter, serverctrls=[req_ctrl])

            groups_list = self.extract_groups(ldap_groups)
        except ldap.LDAPError as err_msg:
            # На случай ошибочности запроса к AD
            msg = _local_(
                "Fail to connect to Authentication Directory. Check service information."
            )
            await system_logger.error(msg, entity=self.entity, description=str(err_msg))
            await self.update(status=Status.FAILED).apply()
            groups_list = list()

        connection.unbind_s()
        return groups_list

    @staticmethod
    def build_ms_ad_group_user_filter(groups_cn: list) -> str:
        base_filter = "(&(sAMAccountName=*)"
        locked_account_filter = "(!(userAccountControl:1.2.840.113556.1.4.803:=2))"
        persons_filter = (
            "(|(objectCategory=USER)(objectCategory=PERSON))(objectClass=USER)"
        )
        member_of_filter = "(memberOf={})".format(groups_cn)
        # Строим итоговый фильтр
        final_filter = "".join(
            [base_filter, locked_account_filter, persons_filter, member_of_filter, ")"]
        )
        return final_filter

    @staticmethod
    def build_free_ipa_group_user_filter(groups_cn: list) -> str:
        persons_filter = "(&(objectclass=posixAccount)(objectclass=person)(!(nsaccountlock=TRUE))"
        extra_filter = "(memberOf={}))".format(groups_cn)
        return persons_filter + extra_filter

    def build_group_user_filter(self, groups_cn: list):
        """Строим фильтр для поиска пользователей членов групп AD."""
        if self.directory_type == self.DirectoryTypes.ActiveDirectory:
            return self.build_ms_ad_group_user_filter(groups_cn)
        elif self.directory_type == self.DirectoryTypes.FreeIPA:
            return self.build_free_ipa_group_user_filter(groups_cn)
        raise NotImplementedError(
            "{} not implemented yet.".format(self.directory_type))

    def extract_ms_ad_group_members(self, ldap_response: Iterable) -> list:
        users_list = list()
        for user in ldap_response:
            ad_search_cn = user[0]
            # Если не указан ad_search_cn - не получится
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
            username = username.decode("utf-8") if username else None
            email = email.decode("utf-8") if email else None
            fullname = fullname.decode("utf-8") if fullname else None
            first_name = first_name.decode("utf-8") if first_name else None
            last_name = last_name.decode("utf-8") if last_name else None

            # Если не указано имя и фамилия - пытаемся разобрать fullname
            if (not first_name or not last_name) and fullname:
                first_name, *last_name = fullname.split()
                if isinstance(last_name, list):
                    last_name = " ".join(last_name)

            # Перепроверяем чтобы при пустой строке был None
            last_name = last_name if last_name else None
            first_name = first_name if first_name else None

            # Нужен как минимум username
            if username:
                users_list.append(
                    {
                        "username": username,
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                    }
                )
        return users_list

    def extract_free_ipa_group_members(self, ldap_response: Iterable) -> list:
        users_list = list()
        for user in ldap_response:
            ad_search_cn = user[0]
            # Если не указан ad_search_cn - не получится
            if not ad_search_cn:
                continue
            for attr in user:
                if isinstance(attr, dict):
                    # Наименование группы AuthenticationDirectory
                    username = unpack_ad_info(attr, self.IPA_USERNAME)
                    email = unpack_ad_info(attr, self.AD_EMAIL)
                    fullname = unpack_ad_info(attr, self.AD_FULLNAME)
                    first_name = unpack_ad_info(attr, self.AD_FIRST_NAME)
                    last_name = unpack_ad_info(attr, self.AD_SURNAME)

                    # Преобразуем bytes-строки
                    username = username.decode("utf-8") if username else None
                    email = email.decode("utf-8") if email else None
                    fullname = fullname.decode("utf-8") if fullname else None
                    first_name = first_name.decode("utf-8") if first_name else None
                    last_name = last_name.decode("utf-8") if last_name else None

                    # Если не указано имя и фамилия - пытаемся разобрать fullname
                    if (not first_name or not last_name) and fullname:
                        first_name, *last_name = fullname.split()
                        if isinstance(last_name, list):
                            last_name = " ".join(last_name)

                    # Перепроверяем чтобы при пустой строке был None
                    last_name = last_name if last_name else None
                    first_name = first_name if first_name else None

                    # Нужен как минимум username
                    if username:
                        users_list.append(
                            {
                                "username": username,
                                "email": email,
                                "first_name": first_name,
                                "last_name": last_name,
                            }
                        )
                        break
        return users_list

    async def get_members_of_ad_group(self, group_cn: str):
        """Пользователи члены группы в Authentication Directory."""
        connection = await self.get_connection()
        if not connection:
            return list()
        users_list = list()
        try:
            # Делаем серию запросов, чтобы извлечь всех пользователей группы
            users_filter = self.build_group_user_filter(group_cn)
            req_ctrl = LdapPageCtrl(criticality=True, size=PAGE_SIZE, cookie="")
            first_loop = True
            final_ldap_response = []

            while first_loop or req_ctrl.cookie:
                first_loop = False
                dc_str = self.convert_dc_str(self.dc_str)
                # async data request
                msgid = connection.search_ext(
                    base=dc_str, scope=ldap.SCOPE_SUBTREE,
                    filterstr=users_filter, serverctrls=[req_ctrl]
                )

                # block and wait for response
                result_type, ldap_response, msgid, serverctrls = connection.result3(msgid)
                final_ldap_response.extend(ldap_response)

                # Get cookie
                req_ctrl.cookie = None
                page_ctrls = [c for c in serverctrls if c.controlType == LdapPageCtrl.controlType]
                if page_ctrls:
                    req_ctrl.cookie = page_ctrls[0].cookie

            # Разбираем ответ от Authentication Directory
            if self.directory_type == self.DirectoryTypes.ActiveDirectory:
                users_list = self.extract_ms_ad_group_members(final_ldap_response)
            elif self.directory_type == self.DirectoryTypes.FreeIPA:
                users_list = self.extract_free_ipa_group_members(final_ldap_response)
        except ldap.LDAPError as err_msg:
            msg = _local_(
                "Fail to connect to Authentication Directory. Check service information."
            )
            await system_logger.error(msg, entity=self.entity, description=str(err_msg))
            await self.update(status=Status.FAILED).apply()
        connection.unbind_s()
        return users_list

    @staticmethod
    async def sync_group(group_info, creator="system"):
        """При необходимости создает группу из Authentication Directory на VDI."""
        group = await GroupModel.query.where(
            GroupModel.verbose_name == group_info["verbose_name"]
        ).gino.first()
        if group:
            await group.update(ad_guid=str(group_info["ad_guid"])).apply()
            return group
        try:
            group = await GroupModel.soft_create(creator=creator, **group_info)
        except UniqueViolationError:
            # Если срабатывает этот сценарий - что-то пошло не по плану
            return await GroupModel.query.where(
                GroupModel.ad_guid == str(group_info["ad_guid"])
            ).gino.first()
        return group

    @staticmethod
    async def sync_users(users_info, creator="system"):
        """При необходимости создает пользователей из Authentication Directory на VDI."""
        users_list = list()
        async with db.transaction():
            new_users_count = 0
            for user_info in users_info:
                username = user_info["username"]
                last_name = user_info.get("last_name")
                first_name = user_info.get("first_name")
                email = user_info.get("email")
                # Ищем пользователя в системе
                user = await UserModel.query.where(
                    UserModel.username == username
                ).gino.first()
                if user:
                    users_list.append(user.id)
                    continue
                # Создаем пользователя
                user = await UserModel.soft_create(
                    username=username,
                    last_name=last_name,
                    first_name=first_name,
                    email=email,
                    by_ad=True,
                    local_password=False,
                    creator=creator,
                )
                if user:
                    users_list.append(user.id)
                    new_users_count += 1
        entity = {"entity_type": EntityType.AUTH, "entity_uuid": None}
        await system_logger.info(
            _local_("{} new users synced from Authentication Directory.").format(
                new_users_count
            ),
            entity=entity,
            user=creator
        )
        return users_list

    async def synchronize_group(self, group_id, creator="system"):
        """Синхронизирует пользователей группы из AD на VDI."""
        group = await GroupModel.get(group_id)
        if not group:
            raise SilentError(_local_("No such Group."))
        if not group.ad_guid:
            raise SilentError(
                _local_(
                    "Group {} is not synchronized by AD.".format(group.verbose_name))
            )
        # Поиск по ID наладить не удалось, поэтому ищем по имени группы.
        ad_group_members = await self.get_members_of_ad_group(group.ad_cn)
        # Добавлено 19.11.2020
        # Если отсутствуют пользователи - покажем ошибку
        if isinstance(ad_group_members, list) and len(ad_group_members) == 0:
            raise SilentError(_local_("There is no users to sync."))
        # Определяем кого нужно исключить
        vdi_group_members = await group.assigned_users
        exclude_user_list = list()
        for vdi_user in vdi_group_members:
            if vdi_user.username not in [
                ad_user["username"] for ad_user in ad_group_members
            ]:
                exclude_user_list.append(vdi_user.id)
        # Исключаем лишних пользователей
        await group.remove_users(user_id_list=exclude_user_list, creator=creator)
        # Синхронизируем пользователей
        new_users = await self.sync_users(ad_group_members, creator=creator)
        # Добавлено 22.10.2020
        # Включаем пользователей в группу
        await group.add_users(user_id_list=new_users, creator=creator)
        return True

    async def synchronize(self, data, creator="system"):
        """Синхронизирует переданные группы на VDI."""
        # Создаем группу
        group_info = {
            "ad_guid": data["group_ad_guid"],
            "verbose_name": data["group_verbose_name"],
            "ad_cn": data["group_ad_cn"],
        }
        group = await self.sync_group(group_info, creator=creator)
        # Синхронизируем пользователей
        await self.synchronize_group(group.id, creator=creator)
        return True


class Mapping(VeilModel):
    """Модель отображения атрибутов пользователя службы каталогов на группы пользователей системы.

    Описание полей:
    - mapping_type: тип атрибута службы каталогов для отображения на группы системы
    - values: список значений атрибутов пользователя службы каталогов
    """

    __tablename__ = "mapping"

    class ValueTypes(Enum):
        """Класс, описывающий доступные типы атрибутов службы каталогов."""

        USER = "USER"
        OU = "OU"
        GROUP = "GROUP"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False, unique=True)
    description = db.Column(db.Unicode(length=255), nullable=True, unique=False)
    value_type = db.Column(AlchemyEnum(ValueTypes), nullable=False, index=True)
    values = db.Column(JSONB(), nullable=False)
    priority = db.Column(db.Integer(), nullable=False, default=0)

    @property
    def entity_type(self):
        return EntityType.AUTH

    @property
    async def assigned_groups(self):
        query = GroupModel.join(
            GroupAuthenticationDirectoryMapping.query.where(
                GroupAuthenticationDirectoryMapping.mapping_id == self.id
            ).alias()
        ).select()
        return await query.gino.load(GroupModel).all()

    @property
    async def possible_groups(self):
        possible_groups_query = (
            GroupModel.join(
                GroupAuthenticationDirectoryMapping.query.where(
                    GroupAuthenticationDirectoryMapping.mapping_id == self.id
                ).alias(),
                isouter=True,
            )
            .select()
            .where((text("anon_1.id is null")))
        )
        return await possible_groups_query.gino.load(GroupModel).all()


class GroupAuthenticationDirectoryMapping(db.Model):
    __tablename__ = "group_authentication_directory_mappings"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    authentication_directory_id = db.Column(
        UUID(),
        db.ForeignKey(AuthenticationDirectory.id, ondelete="CASCADE"),
        nullable=False,
    )
    group_id = db.Column(
        UUID(), db.ForeignKey(GroupModel.id, ondelete="CASCADE"), nullable=False
    )
    mapping_id = db.Column(
        UUID(), db.ForeignKey(Mapping.id, ondelete="CASCADE"), nullable=False
    )


Index(
    "ix_group_auth_mapping",
    GroupAuthenticationDirectoryMapping.authentication_directory_id,
    GroupAuthenticationDirectoryMapping.group_id,
    GroupAuthenticationDirectoryMapping.mapping_id,
    unique=True,
)
