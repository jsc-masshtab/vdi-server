import graphene
from graphene import Enum as GrapheneEnum
import re

from auth.models import AuthenticationDirectory
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, ValidationError
from common.veil_decorators import superuser_required

from database import StatusGraphene


ConntectionTypesGraphene = GrapheneEnum.from_enum(AuthenticationDirectory.ConnectionTypes)
DirectoryTypesGraphene = GrapheneEnum.from_enum(AuthenticationDirectory.DirectoryTypes)


class AuthenticationDirectoryValidator(MutationValidation):
    """Валидатор для сущности AuthenticationDirectory"""

    @staticmethod
    async def validate_id(obj_dict, value):
        pool = await AuthenticationDirectory.get_object(id=value, include_inactive=True)
        if pool:
            return value
        raise ValidationError('No such Authentication Directory.')

    @staticmethod
    async def validate_service_password(obj_dict, value):
        pass_re = re.compile('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@$!%*?&])[A-Za-z0-9@$!%*?&]{8,}$')
        template_name = re.match(pass_re, value)
        if template_name:
            return value
        raise ValidationError(
            'Пароль должен быть не меньше 8 символов, содержать буквы, цифры и спец.символы.')

    @staticmethod
    async def validate_directory_url(obj_dict, value):
        if not re.match(r'^ldap[s]?://[\S]+$', value):
            raise ValidationError(
                'Authentication directory URL should start with ldap(s)://.')
        return value

    @staticmethod
    async def validate_verbose_name(obj_dict, value):
        if len(value) == 0:
            raise ValidationError(
                'Authentication directory verbose name should not be empty.')
        return value


class AuthenticationDirectoryType(graphene.ObjectType):
    """Описание полей:

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

    id = graphene.UUID()
    verbose_name = graphene.String()
    directory_url = graphene.String()
    connection_type = ConntectionTypesGraphene()
    description = graphene.String()
    directory_type = DirectoryTypesGraphene()
    domain_name = graphene.String()

    # SSO fields
    subdomain_name = graphene.String()
    service_username = graphene.String()
    service_password = graphene.String()
    admin_server = graphene.String()
    kdc_urls = graphene.List(graphene.String)
    status = StatusGraphene()
    sso = graphene.Boolean(default_value=False)

    async def resolve_service_password(self, _info):
        return '*' * 8  # dummy value for not displayed field


class AuthenticationDirectoryQuery(graphene.ObjectType):
    auth_dirs = graphene.List(AuthenticationDirectoryType, ordering=graphene.String())
    auth_dir = graphene.Field(AuthenticationDirectoryType, id=graphene.UUID())

    @staticmethod
    def instance_to_type(model_instance):
        return AuthenticationDirectoryType(**model_instance.__values__)

    @superuser_required
    async def resolve_auth_dir(self, info, id=None):
        if not id:
            raise SimpleError('Specify id.')

        auth_dir = await AuthenticationDirectory.get_object(id)
        if not auth_dir:
            raise SimpleError('No such Authentication Directory.')
        return AuthenticationDirectoryQuery.instance_to_type(auth_dir)

    @superuser_required
    async def resolve_auth_dirs(self, info, ordering=None):
        auth_dirs = await AuthenticationDirectory.get_objects(ordering=ordering)
        objects = [
            AuthenticationDirectoryQuery.instance_to_type(auth_dir)
            for auth_dir in auth_dirs
        ]
        return objects


class CreateAuthenticationDirectoryMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        verbose_name = graphene.String(required=True)
        description = graphene.String()
        directory_url = graphene.String(required=True)
        connection_type = ConntectionTypesGraphene()
        directory_type = DirectoryTypesGraphene()
        domain_name = graphene.String(required=True)

        # SSO:
        service_username = graphene.String()
        service_password = graphene.String()
        admin_server = graphene.String()
        subdomain_name = graphene.String()
        kdc_urls = graphene.List(graphene.String)
        sso = graphene.Boolean(default_value=False)

    auth_dir = graphene.Field(lambda: AuthenticationDirectoryType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        auth_dir = await AuthenticationDirectory.soft_create(**kwargs)
        return CreateAuthenticationDirectoryMutation(
            auth_dir=AuthenticationDirectoryType(**auth_dir.__values__),
            ok=True)


class DeleteAuthenticationDirectoryMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        await AuthenticationDirectory.soft_delete(id=kwargs['id'])
        return DeleteAuthenticationDirectoryMutation(ok=True)


class TestAuthenticationDirectoryMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        auth_dir = await AuthenticationDirectory.get_object(kwargs['id'])
        connection_ok = await auth_dir.test_connection()
        return TestAuthenticationDirectoryMutation(ok=connection_ok)


class UpdateAuthenticationDirectoryMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        verbose_name = graphene.String()
        directory_url = graphene.String()
        connection_type = ConntectionTypesGraphene()
        description = graphene.String()
        directory_type = DirectoryTypesGraphene()
        domain_name = graphene.String()
        subdomain_name = graphene.String()
        service_username = graphene.String()
        service_password = graphene.String()
        admin_server = graphene.String()
        kdc_urls = graphene.List(graphene.String)
        sso = graphene.Boolean(default_value=False)

    auth_dir = graphene.Field(lambda: AuthenticationDirectoryType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @superuser_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        auth_dir = await AuthenticationDirectory.soft_update(kwargs['id'],
                                                             kwargs.get('verbose_name'), kwargs.get('directory_url'),
                                                             kwargs.get('connection_type'), kwargs.get('description'),
                                                             kwargs.get('directory_type'), kwargs.get('domain_name'),
                                                             kwargs.get('subdomain_name'),
                                                             kwargs.get('service_username'),
                                                             kwargs.get('service_password'), kwargs.get('admin_server'),
                                                             kwargs.get('kdc_urls'), kwargs.get('sso'),
                                                             )
        return UpdateAuthenticationDirectoryMutation(
            auth_dir=AuthenticationDirectoryType(**auth_dir.__values__),
            ok=True)


class AuthenticationDirectoryMutations(graphene.ObjectType):
    createAuthDir = CreateAuthenticationDirectoryMutation.Field()
    updateAuthDir = UpdateAuthenticationDirectoryMutation.Field()
    testAuthDir = TestAuthenticationDirectoryMutation.Field()
    deleteAuthDir = DeleteAuthenticationDirectoryMutation.Field()


auth_dir_schema = graphene.Schema(mutation=AuthenticationDirectoryMutations,
                                  query=AuthenticationDirectoryQuery,
                                  auto_camelcase=False)
