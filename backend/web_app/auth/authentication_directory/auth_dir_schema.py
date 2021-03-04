# -*- coding: utf-8 -*-
import re
import graphene
from graphene import Enum as GrapheneEnum

from common.database import db
from common.veil.veil_gino import Status, StatusGraphene
from common.veil.veil_validators import MutationValidation
from common.veil.veil_errors import SilentError, ValidationError
from common.veil.veil_decorators import security_administrator_required

from common.models.authentication_directory import AuthenticationDirectory, Mapping
from common.models.auth import Group

from common.languages import lang_init


_ = lang_init()

ConnectionTypesGraphene = GrapheneEnum.from_enum(
    AuthenticationDirectory.ConnectionTypes
)
DirectoryTypesGraphene = GrapheneEnum.from_enum(AuthenticationDirectory.DirectoryTypes)
MappingTypesGraphene = GrapheneEnum.from_enum(Mapping.ValueTypes)


class AuthenticationDirectoryValidator(MutationValidation):
    """Валидатор для сущности AuthenticationDirectory."""

    @staticmethod
    async def validate_id(obj_dict, value):
        ad = await AuthenticationDirectory.get_object(id_=value, include_inactive=True)
        if ad:
            return value
        raise ValidationError(_("No such Authentication Directory."))

    @staticmethod
    async def validate_directory_url(obj_dict, value):
        if not re.match(r"^ldap[s]?://[\S]+$", value):
            raise ValidationError(
                _("Authentication directory URL should start with ldap(s)://.")
            )
        return value

    @staticmethod
    async def validate_verbose_name(obj_dict, value):
        if len(value) == 0:
            raise ValidationError(_("Verbose name should not be empty."))
        return value

    @staticmethod
    async def validate_domain_name(obj_dict, value):
        if not re.match(r"^[a-zA-Z0-9\-_\.]{1,63}$", value):
            raise ValidationError(
                _("Value should be 1-63 latin characters, -, . or _.")
            )
        return value

    @staticmethod
    async def validate_description(obj_dict, value):
        if len(value) == 0:
            value = None
        return value

    @staticmethod
    async def validate_groups(obj_dict, value):
        value_count = len(value)
        if value_count > 0 and isinstance(value, list):
            # Нет желания явно проверять каждого пользователя на присутствие
            exists_count = (
                await db.select([db.func.count()])
                .where(Group.id.in_(value))
                .gino.scalar()
            )
            if exists_count != value_count:
                raise ValidationError(_("users count not much with db count."))
            return value
        raise ValidationError(_("groups list is empty."))

    @staticmethod
    async def validate_mapping_id(obj_dict, value):
        mapping = await Mapping.get(value)
        if mapping:
            return value
        raise ValidationError(_("No such mapping."))

    @staticmethod
    async def validate_dc_str(obj_dict, value):
        if len(value) == 0:
            raise ValidationError(_("DC should not be empty."))
        return value


class MappingGroupType(graphene.ObjectType):
    """Намеренное дублирование GroupType с сокращением доступных полей.

    Нет понимания в целесообразности абстрактного класса для обоих типов.
    """

    id = graphene.UUID(required=True)
    verbose_name = graphene.String()
    description = graphene.String()


class MappingType(graphene.ObjectType):
    id = graphene.UUID()
    verbose_name = graphene.String()
    description = graphene.String()
    value_type = MappingTypesGraphene()
    values = graphene.List(graphene.String)
    priority = graphene.Int()
    status = StatusGraphene()

    assigned_groups = graphene.List(MappingGroupType)
    possible_groups = graphene.List(MappingGroupType)

    async def resolve_assigned_groups(self, _info):
        mapping = await Mapping.get(self.id)
        return await mapping.assigned_groups

    async def resolve_possible_groups(self, _info):
        mapping = await Mapping.get(self.id)
        return await mapping.possible_groups

    async def resolve_status(self, _info):
        # TODO: NotImplemented
        return Status.ACTIVE


class AuthenticationDirectoryGroupType(graphene.ObjectType):
    ad_guid = graphene.UUID()
    verbose_name = graphene.String()
    ad_search_cn = graphene.String()
    id = graphene.UUID()


# Deprecated 22.10.2020
# class AuthenticationDirectoryGroupMembersType(graphene.ObjectType):
#     email = graphene.String()
#     last_name = graphene.String()
#     first_name = graphene.String()
#     username = graphene.String()


# Deprecated 22.10.2020
# class AuthenticationDirectorySyncGroupMembersType(graphene.InputObjectType):
#     """Вложенная в group_members структура.
#        Описывает поля пользователя Authentication Directory."""
#     username = graphene.String(required=True)
#     email = graphene.String()
#     last_name = graphene.String()
#     first_name = graphene.String()


class AuthenticationDirectorySyncGroupType(graphene.InputObjectType):
    """Тип для мутации синхронизации групп/пользователей из Authentication Directory."""

    group_ad_guid = graphene.UUID(required=True)
    group_verbose_name = graphene.String(required=True)
    group_ad_cn = graphene.String(required=True)


class AuthenticationDirectoryType(graphene.ObjectType):
    """Служба каталогов."""

    id = graphene.UUID(description="Внутренний идентификатор")
    verbose_name = graphene.String(description="Имя")
    directory_url = graphene.String(description="Адрес службы каталогов")
    connection_type = ConnectionTypesGraphene(description="Тип подключения")
    description = graphene.String(description="Описание")
    directory_type = DirectoryTypesGraphene(description="Тип службы каталогов")
    domain_name = graphene.String(description="Имя контроллера доменов")
    dc_str = graphene.String(description="Класс объекта домена")
    service_username = graphene.String(
        description="Пользователь имеющий права для управления AD"
    )
    service_password = graphene.String(
        description="Пароль пользователя имеющего права для управления AD"
    )
    status = StatusGraphene(description="Статус")

    mappings = graphene.List(
        MappingType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )

    assigned_ad_groups = graphene.List(AuthenticationDirectoryGroupType)
    possible_ad_groups = graphene.List(AuthenticationDirectoryGroupType)

    async def resolve_service_password(self, _info):
        """Dummy value for not displayed field."""
        return "*" * 7

    async def resolve_mappings(self, _info, limit, offset):
        auth_dir = await AuthenticationDirectory.get(self.id)
        return await auth_dir.mappings_paginator(limit=limit, offset=offset)

    async def resolve_assigned_ad_groups(self, _info):
        """Группы созданные при предыдущих синхронизациях."""
        auth_dir = await AuthenticationDirectory.get(self.id)
        return await auth_dir.assigned_ad_groups

    async def resolve_possible_ad_groups(self, _info):
        """Получить список доступных групп из AuthenticationDirectory."""
        auth_dir = await AuthenticationDirectory.get(self.id)
        groups = await auth_dir.get_possible_ad_groups()
        if groups:
            return groups
        return list()


class AuthenticationDirectoryQuery(graphene.ObjectType):
    auth_dirs = graphene.List(
        AuthenticationDirectoryType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        ordering=graphene.String(),
    )
    auth_dir = graphene.Field(AuthenticationDirectoryType, id=graphene.UUID())

    @staticmethod
    def instance_to_type(model_instance):
        return AuthenticationDirectoryType(**model_instance.__values__)

    @security_administrator_required
    async def resolve_auth_dir(self, info, creator, id=None):
        if not id:
            raise SilentError(_("Specify id."))

        auth_dir = await AuthenticationDirectory.get_object(id)
        if not auth_dir:
            raise SilentError(_("No such Authentication Directory."))
        return AuthenticationDirectoryQuery.instance_to_type(auth_dir)

    @security_administrator_required
    async def resolve_auth_dirs(self, info, limit, offset, creator, ordering=None):
        auth_dirs = await AuthenticationDirectory.get_objects(
            limit, offset, ordering=ordering
        )
        objects = [
            AuthenticationDirectoryQuery.instance_to_type(auth_dir)
            for auth_dir in auth_dirs
        ]
        return objects


class CreateAuthenticationDirectoryMutation(
    graphene.Mutation, AuthenticationDirectoryValidator
):
    class Arguments:
        verbose_name = graphene.String(required=True, description="Имя")
        description = graphene.String(description="Описание")
        directory_url = graphene.String(
            required=True, description="Адрес службы каталогов"
        )
        connection_type = ConnectionTypesGraphene(description="Тип подключения")
        directory_type = DirectoryTypesGraphene(description="Тип службы каталогов")
        domain_name = graphene.String(
            required=True, description="Имя контроллера доменов"
        )
        dc_str = graphene.String(required=True, description="Класс объекта домена")
        service_username = graphene.String(
            description="пользователь имеющий права для управления AD"
        )
        service_password = graphene.String(
            description="пароль пользователя имеющего права для управления AD"
        )

    auth_dir = graphene.Field(lambda: AuthenticationDirectoryType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        auth_dir = await AuthenticationDirectory.soft_create(creator=creator, **kwargs)
        return CreateAuthenticationDirectoryMutation(
            auth_dir=AuthenticationDirectoryType(**auth_dir.__values__), ok=True
        )


class DeleteAuthenticationDirectoryMutation(
    graphene.Mutation, AuthenticationDirectoryValidator
):
    class Arguments:
        id = graphene.UUID(required=True, description="Внутренний идентификатор")

    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        auth_dir = await AuthenticationDirectory.get(kwargs["id"])
        if not auth_dir:
            raise SilentError(_("No such Authentication Directory."))
        status = await auth_dir.soft_delete(creator=creator)
        return DeleteAuthenticationDirectoryMutation(ok=status)


class TestAuthenticationDirectoryMutation(
    graphene.Mutation, AuthenticationDirectoryValidator
):
    class Arguments:
        id = graphene.UUID(required=True, description="Внутренний идентификатор")

    auth_dir = graphene.Field(lambda: AuthenticationDirectoryType)
    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        auth_dir = await AuthenticationDirectory.get_object(kwargs["id"])
        connection_ok = await auth_dir.test_connection()
        auth_dir = await AuthenticationDirectory.get(auth_dir.id)
        return TestAuthenticationDirectoryMutation(ok=connection_ok, auth_dir=auth_dir)


class UpdateAuthenticationDirectoryMutation(
    graphene.Mutation, AuthenticationDirectoryValidator
):
    class Arguments:
        id = graphene.UUID(required=True, description="Внутренний идентификатор")
        verbose_name = graphene.String(description="Имя")
        directory_url = graphene.String(description="Адрес службы каталогов")
        connection_type = ConnectionTypesGraphene(description="Тип подключения")
        description = graphene.String(description="Описание")
        directory_type = DirectoryTypesGraphene(description="Тип службы каталогов")
        domain_name = graphene.String(description="Имя контроллера доменов")
        dc_str = graphene.String(description="Класс объекта домена")
        service_username = graphene.String(
            description="Пользователь имеющий права для управления AD"
        )
        service_password = graphene.String(
            description="Пароль пользователя имеющего права для управления AD"
        )

    auth_dir = graphene.Field(lambda: AuthenticationDirectoryType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        auth_dir = await AuthenticationDirectory.soft_update(
            kwargs["id"],
            verbose_name=kwargs.get("verbose_name"),
            directory_url=kwargs.get("directory_url"),
            connection_type=kwargs.get("connection_type"),
            description=kwargs.get("description"),
            directory_type=kwargs.get("directory_type"),
            domain_name=kwargs.get("domain_name"),
            service_username=kwargs.get("service_username"),
            service_password=kwargs.get("service_password"),
            dc_str=kwargs.get("dc_str"),
            creator=creator,
        )
        return UpdateAuthenticationDirectoryMutation(
            auth_dir=AuthenticationDirectoryType(**auth_dir.__values__), ok=True
        )


class AddAuthDirMappingMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(
            required=True, description="Внутренний идентификатор службы каталогов"
        )
        verbose_name = graphene.String(required=True)
        groups = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))
        values = graphene.NonNull(graphene.List(graphene.NonNull(graphene.String)))
        # Это именно список, потому что на ECP сейчас передается список строк.
        # В БД именно JSON, потому что на ECP - JSON.

        value_type = MappingTypesGraphene(default_value=Mapping.ValueTypes.USER.value)
        priority = graphene.Int(default_value=0)
        description = graphene.String()

    auth_dir = graphene.Field(AuthenticationDirectoryType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        mapping_dict = {
            "verbose_name": kwargs["verbose_name"],
            "description": kwargs.get("description"),
            "value_type": kwargs["value_type"],
            "values": kwargs["values"],
            "priority": kwargs["priority"],
        }
        auth_dir = await AuthenticationDirectory.get(kwargs["id"])
        await auth_dir.add_mapping(
            mapping=mapping_dict, groups=kwargs["groups"], creator=creator
        )
        return AddAuthDirMappingMutation(ok=True, auth_dir=auth_dir)


class DeleteAuthDirMappingMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        mapping_id = graphene.UUID(required=True)

    auth_dir = graphene.Field(AuthenticationDirectoryType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)

        mapping = await Mapping.get(kwargs["mapping_id"])
        auth_dir = await AuthenticationDirectory.get(kwargs["id"])
        status = await mapping.soft_delete(creator=creator)
        return DeleteAuthDirMappingMutation(ok=status, auth_dir=auth_dir)


class EditAuthDirMappingMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        mapping_id = graphene.UUID(required=True)

        verbose_name = graphene.String()
        groups = graphene.List(graphene.UUID)
        values = graphene.List(graphene.String)
        value_type = MappingTypesGraphene()
        priority = graphene.Int()
        description = graphene.String()

    auth_dir = graphene.Field(AuthenticationDirectoryType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)

        mapping_dict = {
            "verbose_name": kwargs.get("verbose_name"),
            "description": kwargs.get("description"),
            "value_type": kwargs.get("value_type"),
            "values": kwargs.get("values"),
            "priority": kwargs.get("priority"),
            "mapping_id": kwargs["mapping_id"],
        }

        auth_dir = await AuthenticationDirectory.get(kwargs["id"])
        await auth_dir.edit_mapping(
            mapping=mapping_dict, groups=kwargs.get("groups"), creator=creator
        )

        return EditAuthDirMappingMutation(ok=True, auth_dir=auth_dir)


class SyncAuthenticationDirectoryGroupUsers(graphene.Mutation):
    class Arguments:
        auth_dir_id = graphene.UUID(required=True)
        sync_data = AuthenticationDirectorySyncGroupType(required=True)

    ok = graphene.Boolean(default_value=False)

    @security_administrator_required
    async def mutate(self, _info, auth_dir_id, sync_data, **kwargs):
        auth_dir = await AuthenticationDirectory.get(auth_dir_id)
        if not auth_dir:
            raise SilentError(_("No such Authentication Directory."))
        await auth_dir.synchronize(sync_data)
        return SyncAuthenticationDirectoryGroupUsers(ok=True)


class SyncExistingAuthenticationDirectoryGroupUsers(graphene.Mutation):
    """Синхронизация существующей группы (ранее синхронизированной)."""

    class Arguments:
        auth_dir_id = graphene.UUID(required=True)
        group_id = graphene.UUID(required=True)

    ok = graphene.Boolean(default_value=False)

    @security_administrator_required
    async def mutate(self, info, auth_dir_id, group_id, **kwargs):
        auth_dir = await AuthenticationDirectory.get(auth_dir_id)
        if not auth_dir:
            raise SilentError(_("No such Authentication Directory."))
        await auth_dir.synchronize_group(group_id)
        return SyncAuthenticationDirectoryGroupUsers(ok=True)


class AuthenticationDirectoryMutations(graphene.ObjectType):
    createAuthDir = CreateAuthenticationDirectoryMutation.Field()
    updateAuthDir = UpdateAuthenticationDirectoryMutation.Field()
    testAuthDir = TestAuthenticationDirectoryMutation.Field()
    deleteAuthDir = DeleteAuthenticationDirectoryMutation.Field()
    addAuthDirMapping = AddAuthDirMappingMutation.Field()
    deleteAuthDirMapping = DeleteAuthDirMappingMutation.Field()
    editAuthDirMapping = EditAuthDirMappingMutation.Field()
    syncAuthDirGroupUsers = SyncAuthenticationDirectoryGroupUsers.Field()
    syncExistAuthDirGroupUsers = SyncExistingAuthenticationDirectoryGroupUsers.Field()


auth_dir_schema = graphene.Schema(
    mutation=AuthenticationDirectoryMutations,
    query=AuthenticationDirectoryQuery,
    auto_camelcase=False,
)
