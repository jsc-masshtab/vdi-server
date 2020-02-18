import graphene
from graphene import Enum as GrapheneEnum
import re

from database import StatusGraphene, db
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, ValidationError
from common.veil_decorators import security_administrator_required, readonly_required

from auth.authentication_directory.models import AuthenticationDirectory, Mapping
from auth.models import Group


ConntectionTypesGraphene = GrapheneEnum.from_enum(AuthenticationDirectory.ConnectionTypes)
DirectoryTypesGraphene = GrapheneEnum.from_enum(AuthenticationDirectory.DirectoryTypes)
MappingTypesGraphene = GrapheneEnum.from_enum(Mapping.ValueTypes)


class AuthenticationDirectoryValidator(MutationValidation):
    """Валидатор для сущности AuthenticationDirectory"""

    @staticmethod
    async def validate_id(obj_dict, value):
        ad = await AuthenticationDirectory.get_object(id=value, include_inactive=True)
        if ad:
            return value
        raise ValidationError('No such Authentication Directory.')

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
                'Verbose name should not be empty.')
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
            exists_count = await db.select([db.func.count()]).where(Group.id.in_(value)).gino.scalar()
            if exists_count != value_count:
                raise ValidationError('users count not much with db count.')
            return value
        raise ValidationError('groups list is empty.')

    @staticmethod
    async def validate_mapping_id(obj_dict, value):
        mapping = await Mapping.get(value)
        if mapping:
            return value
        raise ValidationError('No such mapping.')


class MappingGroupType(graphene.ObjectType):
    """Намеренное дублирование GroupType с сокращением доступных полей.
    Нет понимания в целесообразности абстрактного класса для обоих типов."""
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

    assigned_groups = graphene.List(MappingGroupType)
    possible_groups = graphene.List(MappingGroupType)

    async def resolve_assigned_groups(self, _info):
        mapping = await Mapping.get(self.id)
        return await mapping.assigned_groups

    async def resolve_possible_groups(self, _info):
        mapping = await Mapping.get(self.id)
        return await mapping.possible_groups


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

    mappings = graphene.List(MappingType)

    async def resolve_service_password(self, _info):
        """dummy value for not displayed field"""
        return '********'

    async def resolve_mappings(self, _info):
        auth_dir = await AuthenticationDirectory.get(self.id)
        return await auth_dir.mappings


class AuthenticationDirectoryQuery(graphene.ObjectType):
    auth_dirs = graphene.List(AuthenticationDirectoryType, ordering=graphene.String())
    auth_dir = graphene.Field(AuthenticationDirectoryType, id=graphene.UUID())

    @staticmethod
    def instance_to_type(model_instance):
        return AuthenticationDirectoryType(**model_instance.__values__)

    @readonly_required
    async def resolve_auth_dir(self, info, id=None):
        if not id:
            raise SimpleError('Specify id.')

        auth_dir = await AuthenticationDirectory.get_object(id)
        if not auth_dir:
            raise SimpleError('No such Authentication Directory.')
        return AuthenticationDirectoryQuery.instance_to_type(auth_dir)

    @readonly_required
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
    @security_administrator_required
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
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        await AuthenticationDirectory.soft_delete(id=kwargs['id'])
        return DeleteAuthenticationDirectoryMutation(ok=True)


class TestAuthenticationDirectoryMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @classmethod
    @security_administrator_required
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
    @security_administrator_required
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


class AddAuthDirMappingMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(required=True)  # AuthDir instance
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
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        mapping_dict = {
            'verbose_name': kwargs['verbose_name'],
            'description': kwargs.get('description'),
            'value_type': kwargs['value_type'],
            'values': kwargs['values'],
            'priority': kwargs['priority']
        }
        auth_dir = await AuthenticationDirectory.get(kwargs['id'])
        await auth_dir.add_mapping(mapping=mapping_dict,
                                   groups=kwargs['groups'])
        return AddAuthDirMappingMutation(ok=True, auth_dir=auth_dir)


class DeleteAuthDirMappingMutation(graphene.Mutation, AuthenticationDirectoryValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        mapping_id = graphene.UUID(required=True)

    auth_dir = graphene.Field(AuthenticationDirectoryType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)

        mapping = await Mapping.get(kwargs['mapping_id'])
        await mapping.delete()
        auth_dir = await AuthenticationDirectory.get(kwargs['id'])
        return DeleteAuthDirMappingMutation(ok=True, auth_dir=auth_dir)


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
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)

        mapping_dict = {
            'verbose_name': kwargs.get('verbose_name'),
            'description': kwargs.get('description'),
            'value_type': kwargs.get('value_type'),
            'values': kwargs.get('values'),
            'priority': kwargs.get('priority'),
            'mapping_id': kwargs['mapping_id']
        }

        auth_dir = await AuthenticationDirectory.get(kwargs['id'])
        await auth_dir.edit_mapping(mapping=mapping_dict,
                                    groups=kwargs.get('groups'))

        return EditAuthDirMappingMutation(ok=True, auth_dir=auth_dir)


class AuthenticationDirectoryMutations(graphene.ObjectType):
    createAuthDir = CreateAuthenticationDirectoryMutation.Field()
    updateAuthDir = UpdateAuthenticationDirectoryMutation.Field()
    testAuthDir = TestAuthenticationDirectoryMutation.Field()
    deleteAuthDir = DeleteAuthenticationDirectoryMutation.Field()
    addAuthDirMapping = AddAuthDirMappingMutation.Field()
    deleteAuthDirMapping = DeleteAuthDirMappingMutation.Field()
    editAuthDirMapping = EditAuthDirMappingMutation.Field()


auth_dir_schema = graphene.Schema(mutation=AuthenticationDirectoryMutations,
                                  query=AuthenticationDirectoryQuery,
                                  auto_camelcase=False)
