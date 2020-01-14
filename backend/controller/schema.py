import datetime

import graphene
from graphql import GraphQLError

from common.veil_decorators import superuser_required
from common.veil_errors import SimpleError

from auth.utils import crypto
from controller.client import ControllerClient
from controller.models import Controller
from event.models import Event
from resources_monitoring.resources_monitor_manager import resources_monitor_manager

from database import StatusGraphene


class ControllerType(graphene.ObjectType):
    id = graphene.UUID()
    verbose_name = graphene.String()
    address = graphene.String()
    description = graphene.String()
    status = StatusGraphene()
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

    @superuser_required
    async def mutate(self, _info, verbose_name, address, username,
                     password, ldap_connection, description=None):
        try:
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

            await resources_monitor_manager.add_controller(address)
            msg = 'Successfully added new controller {name} with address {address}.'.format(
                name=controller.verbose_name,
                address=address)
            await Event.create_info(msg)
            return AddControllerMutation(ok=True, controller=ControllerType(**controller.__values__))
        except Exception as E:
            msg = 'Add new controller with address {address}: operation failed.'.format(
                address=address)
            descr = str(E)
            await Event.create_error(msg, description=descr)
            raise SimpleError(msg)


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

    @superuser_required
    async def mutate(self, _info, id, verbose_name, address, username,
                     password, ldap_connection, description=None):
        try:
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

            msg = 'Successfully update controller {id} with address {address}.'.format(
                id=controller.id,
                address=address)
            await Event.create_info(msg)
            return UpdateControllerMutation(ok=True, controller=ControllerType(**controller.__values__))
        except Exception as E:
            msg = 'Update controller {id}: operation failed.'.format(
                id=id)
            descr = str(E)
            await Event.create_error(msg, description=descr)
            raise SimpleError(msg)


class RemoveControllerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        full = graphene.Boolean(required=False)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, id, full=False):
        # TODO: validate active connected resources

        controller = await Controller.query.where(Controller.id == id).gino.first()
        if not controller:
            raise GraphQLError('No such controller.')

        if full:
            ok = await controller.full_delete()
        else:
            ok = await controller.soft_delete()

        # todo:
        #  Есть мысль: прекращать взаимодействие с контроллером по ws перед началом удаления самого контроллера
        #  и возвращать взаимодействие, если контроллер не удалось удалить. Логика в том, чтобы не взаимодействовать
        #  с сущностью, находящейся в удаляемом состоянии.
        await resources_monitor_manager.remove_controller(controller.address)

        return RemoveControllerMutation(ok=ok)


# Only for dev
class RemoveAllControllersMutation(graphene.Mutation):
    class Arguments:
        ok = graphene.Boolean()
        full = graphene.Boolean(required=False)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, full=False):
        controllers = await Controller.query.gino.all()
        for controller in controllers:
            if full:
                await controller.full_delete()
            else:
                await controller.soft_delete()
            await resources_monitor_manager.remove_controller(controller.address)

        return RemoveAllControllersMutation(ok=True)


class ControllerQuery(graphene.ObjectType):
    controllers = graphene.List(lambda: ControllerType)
    controller = graphene.Field(lambda: ControllerType, id=graphene.String())

    @superuser_required
    async def resolve_controllers(self, _info):
        controllers = await Controller.query.gino.all()
        objects = [
            ControllerType(**controller.__values__)
            for controller in controllers
        ]
        return objects

    @superuser_required
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
