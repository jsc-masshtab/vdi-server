import datetime

import graphene
from graphql import GraphQLError

from auth.utils import crypto
from controller.models import Controller
# TODO: добавить, чтобы пароль шифровался через crypto.encrypt


class ControllerType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    address = graphene.String()
    description = graphene.String()
    status = graphene.String()
    version = graphene.String()

    username = graphene.String()
    password = graphene.String()
    ldap_connection = graphene.Boolean()

    token = graphene.String()  # not displayed field
    expires_on = graphene.DateTime()  # not displayed field

    async def resolve_version(self, _info):
        # TODO: get soft version from controller
        return self.version if self.version else '4.0.0'

    async def resolve_status(self, _info):
        # TODO: get status from veil
        return self.status if self.status else 'unknown'

    async def resolve_token(self, _info):
        return '*****'  # dummy value for not displayed field

    async def resolve_expires_on(self, _info):
        return datetime.datetime.now()  # dummy value for not displayed field


class AddController(graphene.Mutation):
    class Arguments:
        verbose_name = graphene.String(required=True)
        address = graphene.String(required=True)
        description = graphene.String()

        username = graphene.String(required=True)
        password = graphene.String(required=True)
        ldap_connection = graphene.Boolean(required=True)

    ok = graphene.Boolean()
    controller = graphene.Field(lambda: ControllerType)

    async def mutate(self, _info, verbose_name, address, username, password, ldap_connection,
                     description=None):
        # TODO: validation
        # check that its possible to log in with given credentials (auth request to controller)

        # TODO: add token
        controller = await Controller.create(
            verbose_name=verbose_name,
            address=address,
            description=description,
            username=username,
            password=password,
            ldap_connection=ldap_connection
        )

        # TODO: add controller to resources_monitor_manager
        return AddController(ok=True, controller=ControllerType(**controller.__values__))


class UpdateController(graphene.Mutation):
    class Arguments:
        id = graphene.String(required=True)
        verbose_name = graphene.String(required=True)
        address = graphene.String(required=True)
        description = graphene.String()

        username = graphene.String(required=True)
        password = graphene.String(required=True)
        ldap_connection = graphene.Boolean(required=True)

    ok = graphene.Boolean()
    controller = graphene.Field(lambda: ControllerType)

    async def mutate(self, _info, id, verbose_name, address, username, password, ldap_connection,
                     description=None):
        controller = await Controller.query.where(Controller.id == id).gino.first()
        if not controller:
            raise GraphQLError('No such controller.')
        else:
            # TODO: validation
            # check that its possible to log in with given credentials (auth request to controller)
            status = await controller.update(
                verbose_name=verbose_name,
                address=address,
                description=description,
                username=username,
                password=password,
                ldap_connection=ldap_connection
            ).apply()
            print(status)

        # TODO: restart monitors
        return UpdateController(ok=True, controller=ControllerType(**controller.__values__))


class RemoveController(graphene.Mutation):
    class Arguments:
        id = graphene.String()

    ok = graphene.Boolean()

    async def mutate(self, info, id):
        # TODO: validation (if exist)
        # TODO: remove connected pools
        status = await Controller.delete.where(Controller.id == id).gino.status()
        print(status)
        # remove controller from resources_monitor_manager
        # resources_monitor_manager.remove_controller(controller_ip)
        return RemoveController(ok=True)


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
    addController = AddController.Field()
    updateController = UpdateController.Field()
    removeController = RemoveController.Field()


controller_schema = graphene.Schema(query=ControllerQuery,
                                    mutation=ControllerMutations,
                                    auto_camelcase=False)
