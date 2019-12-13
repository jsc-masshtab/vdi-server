import graphene
import re

from user.models import User
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, ValidationError
from common.veil_decorators import superuser_required


class UserValidator(MutationValidation):
    """Валидатор для сущности User"""

    @staticmethod
    async def validate_id(obj_dict, value):
        user = await User.get_object(id=value, include_inactive=True)
        if user:
            return value
        raise ValidationError('No such user.')

    @staticmethod
    async def validate_username(obj_dict, value):
        usernamename_re = re.compile('^[a-zA-Z0-9.-_+ ]{3,128}$')
        template_name = re.match(usernamename_re, value)
        if template_name:
            return value
        raise ValidationError(
            'Имя пользователя должно содержать буквы, цифры, _, -, + и быть не короче 3 символов.')

    @staticmethod
    async def validate_email(obj_dict, value):
        email_re = re.compile('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        template_name = re.match(email_re, value)
        if template_name:
            return value
        raise ValidationError(
            'Email должен быть содержать символы латинского алфавита и/или цифры, иметь @ и домен.')

    @staticmethod
    async def validate_password(obj_dict, value):
        return value
        # pass_re = re.compile('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@$!%*?&])[A-Za-z0-9@$!%*?&]{8,}$')
        # template_name = re.match(pass_re, value)
        # if template_name:
        #     return value
        # raise ValidationError(
        #     'Пароль должен быть не меньше 8 символов, содержать буквы, цифры и спец.символы.')


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

    async def resolve_password(self, _info):
        return '*' * 8  # dummy value for not displayed field


class UserQuery(graphene.ObjectType):
    users = graphene.List(UserType, ordering=graphene.String())
    user = graphene.Field(UserType, id=graphene.UUID(), username=graphene.String())

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

    @superuser_required
    async def resolve_user(self, info, id=None, username=None):
        if not id and not username:
            raise SimpleError('Scpecify id or username.')

        user = await User.get_object(id, username)
        if not user:
            raise SimpleError('No such user.')
        return UserQuery.instance_to_type(user)

    @superuser_required
    async def resolve_users(self, info, ordering=None):
        users = await User.get_objects(ordering=ordering)
        objects = [
            UserQuery.instance_to_type(user)
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
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
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
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
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
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        # Назначаем новый пароль
        await User.set_password(kwargs['id'], kwargs['password'])
        return ActivateUserMutation(ok=True)


class ActivateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        # Меняем статус пользователя
        await User.activate(kwargs['id'])
        return ActivateUserMutation(ok=True)


class DeactivateUserMutation(graphene.Mutation, UserValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        # Меняем статус пользователя
        await User.deactivate(kwargs['id'])
        return DeactivateUserMutation(ok=True)


class UserMutations(graphene.ObjectType):
    createUser = CreateUserMutation.Field()
    activateUser = ActivateUserMutation.Field()
    deactivateUser = DeactivateUserMutation.Field()
    updateUser = UpdateUserMutation.Field()
    changeUserPassword = ChangeUserPasswordMutation.Field()


user_schema = graphene.Schema(mutation=UserMutations,
                              query=UserQuery,
                              auto_camelcase=False)
