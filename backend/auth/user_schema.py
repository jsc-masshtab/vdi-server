# -*- coding: utf-8 -*-
import graphene
import re

from auth.models import User
from database import RoleTypeGraphene, Role
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, ValidationError, AssertError
from common.veil_decorators import security_administrator_required

from languages import lang_init

_ = lang_init()


class UserValidator(MutationValidation):
    """Валидатор для сущности User"""

    @staticmethod
    async def validate_id(obj_dict, value):
        user = await User.get_object(id=value, include_inactive=True)
        if user:
            return value
        raise ValidationError(_('No such user.'))

    @staticmethod
    async def validate_username(obj_dict, value):
        user_name_re = re.compile('^[a-zA-Z0-9.-_+]{3,128}$')
        template_name = re.match(user_name_re, value.strip())
        if template_name:
            obj_dict['username'] = value
            return value
        raise AssertError(
            _('username must contain >= 3 chars (letters, digits, _, -, +) and can\'t contain any spaces'))

    @staticmethod
    async def validate_email(obj_dict, value):
        # Проверка на уникальность
        email_is_free = await User.check_email(value)
        if not email_is_free:
            raise ValidationError(_('Email {} is already busy').format(value))

        # Проверка на маску
        email_re = re.compile('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')  # noqa
        template_name = re.match(email_re, value)
        if template_name:
            return value
        raise AssertError(
            _('Email must contain English characters and/or digits, @ and domain name.'))

    @staticmethod
    async def validate_password(obj_dict, value):
        return value
        # pass_re = re.compile('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@$!%*?&])[A-Za-z0-9@$!%*?&]{8,}$')
        # template_name = re.match(pass_re, value)
        # if template_name:
        #     return value
        # raise AssertError(
        #     'Пароль должен быть не меньше 8 символов, содержать буквы, цифры и спец.символы.')

    @staticmethod
    async def validate_first_name(obj_dict, value):
        if len(value) > 32:
            raise AssertError(_('First name length must be <= 32 characters.'))
        return value

    @staticmethod
    async def validate_last_name(obj_dict, value):
        if len(value) > 128:
            raise AssertError(_('Last name length must be <= 128 characters.'))
        return value


class UserGroupType(graphene.ObjectType):
    """Намеренное дублирование GroupType с сокращением доступных полей.
    Нет понимания в целесообразности абстрактного класса для обоих типов."""
    id = graphene.UUID(required=True)
    verbose_name = graphene.String()
    description = graphene.String()

    @staticmethod
    def instance_to_type(model_instance):
        return UserGroupType(id=model_instance.id,
                             verbose_name=model_instance.verbose_name,
                             description=model_instance.description)


class UserType(graphene.ObjectType):
    id = graphene.UUID()
    username = graphene.String()
    password = graphene.String()
    email = graphene.String()
    last_name = graphene.String()
    first_name = graphene.String()

    date_joined = graphene.DateTime()
    date_updated = graphene.DateTime()
    last_login = graphene.DateTime()

    is_superuser = graphene.Boolean()
    is_active = graphene.Boolean()

    assigned_groups = graphene.List(UserGroupType)
    possible_groups = graphene.List(UserGroupType)

    assigned_roles = graphene.List(RoleTypeGraphene)
    possible_roles = graphene.List(RoleTypeGraphene)

    @staticmethod
    def instance_to_type(model_instance):
        return UserType(id=model_instance.id,
                        username=model_instance.username,
                        email=model_instance.email,
                        last_name=model_instance.last_name,
                        first_name=model_instance.first_name,
                        date_joined=model_instance.date_joined,
                        date_updated=model_instance.date_updated,
                        last_login=model_instance.last_login,
                        is_superuser=model_instance.is_superuser,
                        is_active=model_instance.is_active)

    async def resolve_password(self, _info):
        return '*' * 8  # dummy value for not displayed field

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


class UserQuery(graphene.ObjectType):
    users = graphene.List(UserType, ordering=graphene.String())
    user = graphene.Field(UserType, id=graphene.UUID(), username=graphene.String())

    @security_administrator_required
    async def resolve_user(self, info, id=None, username=None):
        if not id and not username:
            raise SimpleError(_('Scpecify id or username.'))

        user = await User.get_object(id, username, include_inactive=True)
        if not user:
            raise SimpleError(_('No such user.'))
        return UserType.instance_to_type(user)

    @security_administrator_required
    async def resolve_users(self, info, ordering=None):
        users = await User.get_objects(ordering=ordering, include_inactive=True)
        objects = [
            UserType.instance_to_type(user)
            for user in users
        ]
        return objects


class CreateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        last_name = graphene.String(required=True)
        first_name = graphene.String(required=True)
        is_superuser = graphene.Boolean(default_value=False)

    user = graphene.Field(lambda: UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        kwargs['username'] = kwargs['username'].strip()
        user = await User.soft_create(**kwargs)
        return CreateUserMutation(
            user=UserType(**user.__values__),
            ok=True)


class UpdateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        username = graphene.String()
        email = graphene.String()
        last_name = graphene.String()
        first_name = graphene.String()
        is_superuser = graphene.Boolean()

    user = graphene.Field(lambda: UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        if kwargs.get('username'):
            kwargs['username'] = kwargs['username'].strip()
        user = await User.soft_update(kwargs['id'],
                                      kwargs.get('username'), kwargs.get('email'),
                                      kwargs.get('last_name'), kwargs.get('first_name'),
                                      kwargs.get('is_superuser'))
        return UpdateUserMutation(
            user=UserType(**user.__values__),
            ok=True)


class ChangeUserPasswordMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        # Назначаем новый пароль
        user = await User.get(kwargs['id'])
        if user:
            await user.set_password(kwargs['password'])
            return ChangeUserPasswordMutation(ok=True)
        return ChangeUserPasswordMutation(ok=False)


class ActivateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        # Меняем статус пользователя
        user = await User.get(kwargs['id'])
        if user:
            await user.activate()
            return ActivateUserMutation(ok=True)
        return ActivateUserMutation(ok=False)


class DeactivateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        # Меняем статус пользователя
        user = await User.get(kwargs['id'])
        if user:
            await user.deactivate()
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
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        user = await User.get(kwargs['id'])
        await user.add_roles(kwargs['roles'])
        return AddUserRoleMutation(user=UserType(**user.__values__), ok=True)


class RemoveUserRoleMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    user = graphene.Field(UserType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        user = await User.get(kwargs['id'])
        await user.remove_roles(kwargs['roles'])
        return RemoveUserRoleMutation(user=UserType(**user.__values__), ok=True)


class UserMutations(graphene.ObjectType):
    createUser = CreateUserMutation.Field()
    activateUser = ActivateUserMutation.Field()
    deactivateUser = DeactivateUserMutation.Field()
    updateUser = UpdateUserMutation.Field()
    changeUserPassword = ChangeUserPasswordMutation.Field()
    addUserRole = AddUserRoleMutation.Field()
    removeUserRole = RemoveUserRoleMutation.Field()
    # TODO: добавление групп пользователю


user_schema = graphene.Schema(mutation=UserMutations,
                              query=UserQuery,
                              auto_camelcase=False)
