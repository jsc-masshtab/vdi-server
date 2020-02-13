# -*- coding: utf-8 -*-
import graphene

from database import db, RoleTypeGraphene, Role
from auth.models import Group, User
from common.veil_validators import MutationValidation
from common.veil_errors import SimpleError, ValidationError
from common.veil_decorators import security_administrator_required, readonly_required
from auth.user_schema import UserType


class GroupValidator(MutationValidation):
    """Валидатор для сущности Group"""

    @staticmethod
    async def validate_id(obj_dict, value):
        group = await Group.get(value)
        if group:
            obj_dict['group'] = group
            return value
        raise ValidationError('No such group.')

    @staticmethod
    async def validate_verbose_name(obj_dict, value):
        if len(value) > 0:
            return value
        raise ValidationError('verbose_name is empty.')

    @staticmethod
    async def validate_users(obj_dict, value):
        value_count = len(value)
        if value_count > 0 and isinstance(value, list):
            # Нет желания явно проверять каждого пользователя на присутствие
            exists_count = await db.select([db.func.count()]).where(User.id.in_(value)).gino.scalar()
            if exists_count != value_count:
                raise ValidationError('users count not much with db count.')
            return value
        raise ValidationError('users list is empty.')


class GroupType(graphene.ObjectType):
    id = graphene.UUID(required=True)
    verbose_name = graphene.String()
    description = graphene.String()
    date_created = graphene.DateTime()
    date_updated = graphene.DateTime()

    assigned_users = graphene.List(UserType)
    possible_users = graphene.List(UserType)

    assigned_roles = graphene.List(RoleTypeGraphene)
    possible_roles = graphene.List(RoleTypeGraphene)

    @staticmethod
    def instance_to_type(model_instance):
        return GroupType(id=model_instance.id,
                         verbose_name=model_instance.verbose_name,
                         description=model_instance.description,
                         date_created=model_instance.date_created,
                         date_updated=model_instance.date_updated)

    async def resolve_assigned_users(self, _info):
        group = await Group.get(self.id)
        return await group.assigned_users

    async def resolve_possible_users(self, _info):
        group = await Group.get(self.id)
        return await group.possible_users

    async def resolve_assigned_roles(self, _info):
        group = await Group.get(self.id)
        roles = await group.roles
        return [role_type.role for role_type in roles]

    async def resolve_possible_roles(self, _info):
        assigned_roles = await self.resolve_assigned_roles(_info)
        all_roles = [role_type for role_type in Role]
        # Чтобы порядок всегда был одинаковый
        possible_roles = [role for role in all_roles if role not in assigned_roles]
        return possible_roles


class GroupQuery(graphene.ObjectType):
    groups = graphene.List(GroupType, ordering=graphene.String())
    group = graphene.Field(GroupType, id=graphene.UUID())

    @readonly_required
    async def resolve_group(self, info, id):  # noqa
        group = await Group.get(id)
        if not group:
            raise SimpleError('No such group.')
        return GroupType.instance_to_type(group)

    @readonly_required
    async def resolve_groups(self, info, ordering=None):  # noqa
        groups = await Group.get_objects(ordering=ordering, include_inactive=True)
        objects = [
            GroupType.instance_to_type(group)
            for group in groups
        ]
        return objects


class CreateGroupMutation(graphene.Mutation, GroupValidator):
    class Arguments:
        verbose_name = graphene.String(required=True)
        description = graphene.String(required=False)

    group = graphene.Field(GroupType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        group = await Group.create(verbose_name=kwargs['verbose_name'],
                                   description=kwargs.get('description'))

        return CreateGroupMutation(
            group=GroupType(**group.__values__),
            ok=True)


class UpdateGroupMutation(graphene.Mutation, GroupValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        verbose_name = graphene.String(required=False)
        description = graphene.String(required=False)

    group = graphene.Field(GroupType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        group = await Group.get(kwargs['id'])
        await group.soft_update(verbose_name=kwargs.get('verbose_name'), description=kwargs.get('description'))

        return UpdateGroupMutation(
            group=GroupType(**group.__values__),
            ok=True)


class DeleteGroupMutation(graphene.Mutation, GroupValidator):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        status = await Group.delete.where(Group.id == kwargs['id']).gino.status()
        return DeleteGroupMutation(ok=status)


class AddGroupUsersMutation(graphene.Mutation, GroupValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        users = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))

    group = graphene.Field(GroupType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)

        group = await Group.get(kwargs['id'])
        await group.add_users(kwargs['users'])

        return AddGroupUsersMutation(
            group=GroupType(**group.__values__),
            ok=True)


class RemoveGroupUsersMutation(graphene.Mutation, GroupValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        users = graphene.NonNull(graphene.List(graphene.NonNull(graphene.UUID)))

    group = graphene.Field(GroupType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        group = await Group.get(kwargs['id'])

        async with db.transaction():
            users = kwargs['users']
            status = await group.remove_users(users)

        return RemoveGroupUsersMutation(
            group=GroupType(**group.__values__),
            ok=status)


class AddGroupRoleMutation(graphene.Mutation, GroupValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    group = graphene.Field(GroupType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        group = await Group.get(kwargs['id'])
        await group.add_roles(kwargs['roles'])
        return AddGroupRoleMutation(group=GroupType(**group.__values__), ok=True)


class RemoveGroupRoleMutation(graphene.Mutation, GroupValidator):
    class Arguments:
        id = graphene.UUID(required=True)
        roles = graphene.NonNull(graphene.List(graphene.NonNull(RoleTypeGraphene)))

    group = graphene.Field(GroupType)
    ok = graphene.Boolean(default_value=False)

    @classmethod
    @security_administrator_required
    async def mutate(cls, root, info, **kwargs):
        await cls.validate_agruments(**kwargs)
        group = await Group.get(kwargs['id'])
        await group.remove_roles(kwargs['roles'])
        return RemoveGroupRoleMutation(group=GroupType(**group.__values__), ok=True)


class GroupMutations(graphene.ObjectType):
    createGroup = CreateGroupMutation.Field()
    updateGroup = UpdateGroupMutation.Field()
    deleteGroup = DeleteGroupMutation.Field()
    addGroupUsers = AddGroupUsersMutation.Field()
    removeGroupUsers = RemoveGroupUsersMutation.Field()
    addGroupRole = AddGroupRoleMutation.Field()
    removeGroupRole = RemoveGroupRoleMutation.Field()


group_schema = graphene.Schema(query=GroupQuery,
                               mutation=GroupMutations,
                               auto_camelcase=False)
