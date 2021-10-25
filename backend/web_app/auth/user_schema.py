# -*- coding: utf-8 -*-
import re

import graphene
from graphene import Enum as GrapheneEnum

from sqlalchemy import and_

from common.database import db
from common.graphene_utils import ShortString
from common.languages import _local_
from common.models.auth import User
from common.models.user_tk_permission import TkPermission
from common.veil.veil_decorators import security_administrator_required
from common.veil.veil_errors import AssertError, SimpleError, ValidationError
from common.veil.veil_gino import Role, RoleTypeGraphene
from common.veil.veil_validators import MutationValidation

PermissionTypeGraphene = GrapheneEnum.from_enum(TkPermission)


class UserValidator(MutationValidation):
    """Валидатор для сущности User."""

    @staticmethod
    async def validate_id(obj_dict, value):
        user = await User.get_object(id_=value, include_inactive=True)
        if user:
            return value
        raise ValidationError(_local_("No such user."))

    @staticmethod
    async def validate_username(obj_dict, value):
        if not value:
            raise AssertError(_local_("username can`t be empty."))
        user_name_re = re.compile("^[a-zA-Z][a-zA-Z0-9.-_+]{3,128}$")
        template_name = re.match(user_name_re, value.strip())
        if template_name:
            obj_dict["username"] = value
            return value
        raise AssertError(
            _local_(
                "username must contain >= 1 chars (letters, digits, _, -, +), begin from letter and can't contain any spaces."
            )
        )

    @staticmethod
    async def validate_email(obj_dict, value):
        # Проверка на уникальность
        email_is_free = await User.check_email(value)
        if not email_is_free:
            raise ValidationError(_local_("Email {} is already busy.").format(value))

        # Проверка на маску
        email_re = re.compile(
            "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"  # noqa: W605
        )
        template_name = re.match(email_re, value)
        if len(value) == 0:
            return None
        elif template_name:
            return value
        raise AssertError(
            _local_(
                "Email must contain English characters and/or digits, @ and domain name.")
        )

    @staticmethod
    async def validate_password(obj_dict, value):
        # return value
        # TODO: СМЕНИТЬ НА ВАЛИДАЦИЮ ОТНОСИТЕЛЬНО ВЫБРАННОЙ БЕЗОПАСНОСТИ В АСТРЕ
        pass_re = re.compile("^[a-zA-Z0-9@$#^/!<>,`~%*?&._-]{8,32}$")
        template_name = re.match(pass_re, value)
        if template_name:
            return value
        # raise AssertError(
        #     'Пароль должен быть не меньше 8 символов, содержать буквы, цифры и спец.символы.')
        raise AssertError(_local_(
            "Password must contain letters and/or digits, special characters; also be at least 8 characters."))

    @staticmethod
    async def validate_first_name(obj_dict, value):
        if len(value) > 32:
            raise AssertError(_local_("First name length must be <= 32 characters."))
        return value

    @staticmethod
    async def validate_last_name(obj_dict, value):
        if len(value) > 128:
            raise AssertError(_local_("Last name length must be <= 128 characters."))
        return value


class UserGroupType(graphene.ObjectType):
    """Намеренное дублирование GroupType с сокращением доступных полей.

    Нет понимания в целесообразности абстрактного класса для обоих типов.
    """

    id = graphene.UUID(required=True)
    verbose_name = graphene.Field(ShortString)
    description = graphene.Field(ShortString)

    @staticmethod
    def instance_to_type(model_instance):
        return UserGroupType(
            id=model_instance.id,
            verbose_name=model_instance.verbose_name,
            description=model_instance.description,
        )


class GroupInput(graphene.InputObjectType):
    """Инпут ввода групп для пользователя."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)


class UserType(graphene.ObjectType):
    id = graphene.UUID()
    username = graphene.Field(ShortString)
    password = graphene.Field(ShortString)
    email = graphene.Field(ShortString)
    last_name = graphene.Field(ShortString)
    first_name = graphene.Field(ShortString)

    date_joined = graphene.DateTime()
    date_updated = graphene.DateTime()
    last_login = graphene.DateTime()

    is_superuser = graphene.Boolean()
    is_active = graphene.Boolean()

    two_factor = graphene.Boolean()
    secret = graphene.Field(ShortString)

    by_ad = graphene.Boolean()
    local_password = graphene.Boolean()

    assigned_groups = graphene.List(UserGroupType)
    possible_groups = graphene.List(UserGroupType)

    assigned_roles = graphene.List(RoleTypeGraphene)
    possible_roles = graphene.List(RoleTypeGraphene)

    assigned_permissions = graphene.List(
        PermissionTypeGraphene, description="Назначенные разрешения"
    )
    possible_permissions = graphene.List(
        PermissionTypeGraphene, description="Разрешения, которые можно назначить"
    )

    @staticmethod
    def instance_to_type(model_instance):
        return UserType(
            id=model_instance.id,
            username=model_instance.username,
            email=model_instance.email,
            last_name=model_instance.last_name,
            first_name=model_instance.first_name,
            date_joined=model_instance.date_joined,
            date_updated=model_instance.date_updated,
            last_login=model_instance.last_login,
            is_active=model_instance.is_active,
            two_factor=model_instance.two_factor,
            secret=model_instance.secret,
            by_ad=model_instance.by_ad,
            local_password=model_instance.local_password
        )

    async def resolve_is_superuser(self, _info):
        user = await User.get(self.id)
        return await user.superuser()

    async def resolve_password(self, _info):
        return "*" * 8  # dummy value for not displayed field

    async def resolve_assigned_groups(self, _info):
        user = await User.get(self.id)
        return await user.assigned_groups

    async def resolve_possible_groups(self, _info):
        user = await User.get(self.id)
        return await user.possible_groups

    async def resolve_assigned_roles(self, _info):
        """Отображается объединение пользовательский ролей с ролями пользовательских групп."""
        user = await User.get(self.id)
        return await user.roles

    async def resolve_possible_roles(self, _info):
        user = await User.get(self.id)
        assigned_roles = await user.roles
        all_roles = [role_type for role_type in Role]
        # Чтобы порядок всегда был одинаковый
        possible_roles = [role for role in all_roles if role not in assigned_roles]
        return possible_roles

    # permissions
    async def resolve_assigned_permissions(self, _info):
        user = await User.get(self.id)
        return await user.get_permissions()

    async def resolve_possible_permissions(self, _info):
        user = await User.get(self.id)
        assigned_permissions = await user.get_permissions()
        all_permissions = [permission_type for permission_type in TkPermission]

        possible_permissions = [
            perm for perm in all_permissions if perm not in assigned_permissions
        ]
        return possible_permissions


class UserQuery(graphene.ObjectType):
    users = graphene.List(
        lambda: UserType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        username=ShortString(),
        is_superuser=graphene.Boolean(),
        is_active=graphene.Boolean(),
        ordering=ShortString(),
    )
    user = graphene.Field(UserType, id=graphene.UUID(), username=ShortString())

    count = graphene.Int(is_superuser=graphene.Boolean(), is_active=graphene.Boolean())

    existing_permissions = graphene.List(
        PermissionTypeGraphene, description="Существующие разрешения"
    )

    async def resolve_existing_permissions(self, info, **kwargs):
        all_existing_permissions = [permission_type for permission_type in TkPermission]
        return all_existing_permissions

    async def resolve_count(self, info, is_superuser=None, is_active=None, **kwargs):
        if is_superuser:
            superuser_subquery = await User.get_superuser_ids_subquery()
        else:
            superuser_subquery = None
        filters = UserQuery.build_filters(superuser_subquery, is_active)
        query = User.select("id").where(and_(*filters))
        users_count = (
            await db.select([db.func.count()]).select_from(query.alias()).gino.scalar()
        )
        return users_count

    @staticmethod
    def build_filters(superuser_subquery, is_active):
        filters = []
        if superuser_subquery is not None:
            filters.append((User.id.in_(superuser_subquery)))
        if is_active is not None:
            filters.append((User.is_active == is_active))

        return filters

    @security_administrator_required
    async def resolve_user(self, info, id=None, username=None, **kwargs):
        if not id and not username:
            raise SimpleError(_local_("Specify id or username."))

        user = await User.get_object(id, username, include_inactive=True)
        if not user:
            raise SimpleError(_local_("No such user."))
        return UserType.instance_to_type(user)

    @security_administrator_required
    async def resolve_users(
        self,
        info,
        limit,
        offset,
        username=None,
        is_superuser=None,
        is_active=None,
        ordering=None,
        **kwargs
    ):
        if is_superuser:
            superuser_subquery = await User.get_superuser_ids_subquery()
        else:
            superuser_subquery = None

        filters = UserQuery.build_filters(superuser_subquery, is_active)

        users = await User.get_objects(
            limit,
            offset,
            name=username,
            filters=filters,
            ordering=ordering,
            include_inactive=True,
        )
        objects = [UserType.instance_to_type(user) for user in users]
        return objects


class CreateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        username = ShortString(required=True)
        password = ShortString(required=True)
        email = ShortString(required=False)
        last_name = ShortString(required=False)
        first_name = ShortString(required=False)
        groups = graphene.NonNull(graphene.List(GroupInput))
        is_superuser = graphene.Boolean(default_value=False)

    user = graphene.Field(lambda: UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        username = kwargs["username"]
        kwargs["username"] = username.strip() if username else None
        if not kwargs["username"]:
            return CreateUserMutation(ok=False)
        user = await User.soft_create(creator=creator, **kwargs)
        return CreateUserMutation(user=UserType(**user.__values__), ok=True)


class UpdateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        email = ShortString()
        last_name = ShortString()
        first_name = ShortString()
        is_superuser = graphene.Boolean()
        two_factor = graphene.Boolean()

    user = graphene.Field(lambda: UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        user = await User.soft_update(creator=creator, **kwargs)
        return UpdateUserMutation(user=UserType(**user.__values__), ok=True)


class ChangeUserPasswordMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        password = ShortString(required=True)

    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        # Назначаем новый пароль
        user = await User.get(kwargs["id"])
        if user:
            await user.set_password(kwargs["password"], creator=creator)
            return ChangeUserPasswordMutation(ok=True)
        return ChangeUserPasswordMutation(ok=False)


class ActivateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        # Меняем статус пользователя
        user = await User.get(kwargs["id"])
        if user:
            await user.activate(creator=creator)
            return ActivateUserMutation(ok=True)
        return ActivateUserMutation(ok=False)


class DeactivateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        # Меняем статус пользователя
        user = await User.get(kwargs["id"])
        if user:
            await user.deactivate(creator=creator)
            return DeactivateUserMutation(ok=True)
        return DeactivateUserMutation(ok=False)


class AddUserRoleMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    user = graphene.Field(UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        user = await User.get(kwargs["id"])
        await user.add_roles(kwargs["roles"], creator=creator)
        return AddUserRoleMutation(user=UserType(**user.__values__), ok=True)


class RemoveUserRoleMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    user = graphene.Field(UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        user = await User.get(kwargs["id"])
        await user.remove_roles(kwargs["roles"], creator=creator)
        return RemoveUserRoleMutation(user=UserType(**user.__values__), ok=True)


class GenerateUserQrcodeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)

    qr_uri = ShortString()
    secret = ShortString()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        user = await User.get(kwargs["id"])
        data_dict = await user.generate_qr(creator=creator)
        return GenerateUserQrcodeMutation(qr_uri=data_dict["qr_uri"], secret=data_dict["secret"])


# permissions
class AddUserPermissionMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        permissions = graphene.NonNull(
            graphene.List(graphene.NonNull(PermissionTypeGraphene))
        )

    user = graphene.Field(UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)
        user = await User.get(kwargs["id"])
        await user.add_permissions(kwargs["permissions"], creator=creator)
        return AddUserPermissionMutation(user=UserType(**user.__values__), ok=True)


class RemoveUserPermissionMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        permissions = graphene.NonNull(
            graphene.List(graphene.NonNull(PermissionTypeGraphene))
        )

    user = graphene.Field(UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, creator, **kwargs):
        await cls.validate(**kwargs)

        user = await User.get(kwargs["id"])
        await user.remove_permissions(kwargs["permissions"], creator=creator)

        # Посмотреть не содержатся ли разрешения в группах, в которые включен пользователь и
        # сообщить, что убрать эти разрешения нельзя, пока пользователь в соответствующей группе.
        # Без этого админу будет неочевидно (если он не держит в голове инфу о группах),
        # почему у пользователя не убирается разрешение не смотря на положительный ответ.
        permissions_from_group = await user.get_permissions_from_groups()
        permissions_from_group = [
            permission.value for permission in permissions_from_group
        ]
        # check if two lists have at least one common element
        arg_permissions_set = set(kwargs["permissions"])
        # print('arg_permissions_set ', arg_permissions_set, flush=True)
        permissions_from_group_set = set(permissions_from_group)
        # print('permissions_from_group_set ', permissions_from_group_set, flush=True)
        common_permissions = arg_permissions_set & permissions_from_group_set

        if common_permissions:
            common_permissions_str = ", ".join(common_permissions)
            raise SimpleError(
                _local_(
                    "Can`t remove permission(s) {} because they are granted to groups of user {}."
                ).format(common_permissions_str, user.username),
                user=creator,
            )

        return RemoveUserPermissionMutation(user=UserType(**user.__values__), ok=True)


class UserMutations(graphene.ObjectType):
    createUser = CreateUserMutation.Field()
    activateUser = ActivateUserMutation.Field()
    deactivateUser = DeactivateUserMutation.Field()
    updateUser = UpdateUserMutation.Field()
    changeUserPassword = ChangeUserPasswordMutation.Field()
    addUserRole = AddUserRoleMutation.Field()
    removeUserRole = RemoveUserRoleMutation.Field()
    generateUserQrcode = GenerateUserQrcodeMutation.Field()

    addUserPermission = AddUserPermissionMutation.Field()
    removeUserPermission = RemoveUserPermissionMutation.Field()


user_schema = graphene.Schema(
    mutation=UserMutations, query=UserQuery, auto_camelcase=False
)
