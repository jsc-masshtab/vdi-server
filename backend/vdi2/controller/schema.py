import datetime

import graphene
from graphql import GraphQLError

from auth.utils import crypto
from controller.client import ControllerClient
from controller.models import Controller
from resources_monitoring.resources_monitor_manager import resources_monitor_manager


class ControllerType(graphene.ObjectType):
    id = graphene.UUID()
    verbose_name = graphene.String()
    address = graphene.String()
    description = graphene.String()
    status = graphene.String()
    version = graphene.String()

    username = graphene.String()
    password = graphene.String()  # not displayed field
    ldap_connection = graphene.Boolean()

    token = graphene.String()  # not displayed field
    expires_on = graphene.DateTime()  # not displayed field

    async def resolve_status(self, _info):
        # TODO: get status from veil
        return self.status if self.status else 'unknown'

    async def resolve_password(self, _info):
        return '*****'  # dummy value for not displayed field

    async def resolve_token(self, _info):
        return '*****'  # dummy value for not displayed field

    async def resolve_expires_on(self, _info):
        return datetime.datetime.now()  # dummy value for not displayed field


class AddControllerMutation(graphene.Mutation):
    class Arguments:
        verbose_name = graphene.String(required=True)
        address = graphene.String(required=True)
        description = graphene.String()

        username = graphene.String(required=True)
        password = graphene.String(required=True)
        ldap_connection = graphene.Boolean(required=True)

    ok = graphene.Boolean()
    controller = graphene.Field(lambda: ControllerType)

    async def mutate(self, _info, verbose_name, address, username,
                     password, ldap_connection, description=None):
        print('AddControllerMutation::mutate')
        # check credentials
        controller_client = ControllerClient(address)
        auth_info = dict(username=username, password=password, ldap=ldap_connection)
        token, expires_on = await controller_client.auth(auth_info=auth_info)
        version = await controller_client.fetch_version()

        controller = await Controller.create(
            verbose_name=verbose_name,
            address=address,
            description=description,
            version=version,
            status='ACTIVE',  # TODO: special class for all statuses
            username=username,
            password=crypto.encrypt(password),
            ldap_connection=ldap_connection,
            token=token,
            expires_on=expires_on
        )

        resources_monitor_manager.add_controller(address)
        return AddControllerMutation(ok=True, controller=ControllerType(**controller.__values__))


class UpdateControllerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        verbose_name = graphene.String(required=True)
        address = graphene.String(required=True)
        description = graphene.String()

        username = graphene.String(required=True)
        password = graphene.String(required=True)
        ldap_connection = graphene.Boolean(required=True)

    ok = graphene.Boolean()
    controller = graphene.Field(lambda: ControllerType)

    async def mutate(self, _info, verbose_name, address, username,
                     password, ldap_connection, description=None):
        # TODO: update only mutated fields

        controller = await Controller.query.where(Controller.id == id).gino.first()
        if not controller:
            raise GraphQLError('No such controller.')

        # check credentials
        controller_client = ControllerClient(address)
        auth_info = dict(username=username, password=password, ldap=ldap_connection)
        token, expires_on = await controller_client.auth(auth_info=auth_info)
        version = await controller_client.fetch_version()

        await controller.update(
            verbose_name=verbose_name,
            address=address,
            description=description,
            version=version,
            username=username,
            password=crypto.encrypt(password),
            ldap_connection=ldap_connection,
            token=token,
            expires_on=expires_on
        ).apply()

        # TODO: change to update & restart
        await resources_monitor_manager.remove_controller(address)
        await resources_monitor_manager.add_controller(address)
        return UpdateControllerMutation(ok=True, controller=ControllerType(**controller.__values__))


class RemoveControllerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    async def mutate(self, _info, id):
        # TODO: validate active connected resources

        controller = await Controller.query.where(Controller.id == id).gino.first()
        if not controller:
            raise GraphQLError('No such controller.')

        # TODO: remove connected pools
        status = await Controller.delete.where(Controller.id == id).gino.status()
        print(status)

        await resources_monitor_manager.remove_controller(controller.address)
        return RemoveControllerMutation(ok=True)


# Only for dev
class RemoveAllControllersMutation(graphene.Mutation):
    class Arguments:
        ok = graphene.Boolean()

    ok = graphene.Boolean()

    async def mutate(self, _info):
        controllers = await Controller.query.gino.all()
        for controller in controllers:
            await controller.delete()

            # # TODO: remove connected pools
            # status = await Controller.delete.where(Controller.id == id).gino.status()
            # print(status)

            await resources_monitor_manager.remove_controller(controller.address)
        return RemoveAllControllersMutation(ok=True)


class ControllerQuery(graphene.ObjectType):
    controllers = graphene.List(lambda: ControllerType)
    controller = graphene.Field(lambda: ControllerType, id=graphene.String())

    async def resolve_controllers(self, _info):
        controllers = await Controller.query.gino.all()
        objects = [
            ControllerType(**controller.__values__)
            for controller in controllers
        ]
        return objects

    async def resolve_controller(self, _info, id):
        controller = await Controller.query.where(Controller.id == id).gino.first()
        if not controller:
            raise GraphQLError('No such controller.')
        return ControllerType(**controller.__values__)


class ControllerMutations(graphene.ObjectType):
    addController = AddControllerMutation.Field()
    updateController = UpdateControllerMutation.Field()
    removeController = RemoveControllerMutation.Field()
    removeAllControllers = RemoveAllControllersMutation.Field()


controller_schema = graphene.Schema(query=ControllerQuery,
                                    mutation=ControllerMutations,
                                    auto_camelcase=False)
