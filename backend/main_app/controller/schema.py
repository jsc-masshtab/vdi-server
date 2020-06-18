# -*- coding: utf-8 -*-
import graphene
from graphql import GraphQLError

from common.veil_decorators import administrator_required
from common.veil_errors import SimpleError

from database import StatusGraphene
from controller.models import Controller

from languages import lang_init
from journal.journal import Log as log

from redis_broker import send_cmd_to_ws_monitor, WsMonitorCmd


_ = lang_init()

# TODO: перенести добавление контроллера в ресурс монитор в методы модели, чтобы сократить дублирование кода.


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
        return '--'


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

    @administrator_required
    async def mutate(self, _info, verbose_name, address, username,
                     password, ldap_connection, creator, description=None):
        try:
            if len(verbose_name) < 1:
                raise SimpleError(_('Controller name cannot be empty.'))
            controller = await Controller.soft_create(verbose_name, address, username, password, ldap_connection,
                                                      description, creator)
            send_cmd_to_ws_monitor(address, WsMonitorCmd.ADD_CONTROLLER)

            return AddControllerMutation(ok=True, controller=ControllerType(**controller.__values__))
        # except SimpleError as E:
        #     raise SimpleError(E)
        except ValueError as err:
            msg = _('Add new controller {}: operation failed.').format(address)
            description = str(err)
            raise SimpleError(msg, description=description)
        except Exception as E:
            log.debug(E)
            msg = _('Add new controller {}: operation failed.').format(address)
            raise SimpleError(msg)


class UpdateControllerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        verbose_name = graphene.String()
        address = graphene.String()
        description = graphene.String()
        username = graphene.String()
        password = graphene.String()
        ldap_connection = graphene.Boolean()

    ok = graphene.Boolean()
    controller = graphene.Field(lambda: ControllerType)

    @administrator_required
    async def mutate(self, _info, id, creator, verbose_name=None, address=None, username=None,
                     password=None, ldap_connection=None, description=None):
        controller = await Controller.get(id)
        if not controller:
            raise SimpleError(_('No such controller.'))

        try:
            await controller.soft_update(verbose_name=verbose_name,
                                         address=address,
                                         description=description,
                                         username=username,
                                         password=password,
                                         ldap_connection=ldap_connection,
                                         creator=creator
                                         )
        except ValueError:
            msg = _('Fail to update controller {}').format(id)
            raise SimpleError(msg)

        return UpdateControllerMutation(ok=True)


class RemoveControllerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        full = graphene.Boolean(required=False)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, id, creator, full=False):
        # TODO: validate active connected resources

        controller = await Controller.query.where(Controller.id == id).gino.first()
        if not controller:
            raise GraphQLError(_('No such controller.'))

        if full:
            status = await controller.full_delete(creator=creator)
        else:
            status = await controller.soft_delete(dest=_('Controller'), creator=creator)

        if controller.active:
            send_cmd_to_ws_monitor(controller.address, WsMonitorCmd.REMOVE_CONTROLLER)

        return RemoveControllerMutation(ok=status)


class TestControllerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, id, creator):
        controller = await Controller.get(id)
        if not controller:
            raise GraphQLError(_('No such controller.'))
        connection_ok = await controller.check_credentials()
        if connection_ok:
            send_cmd_to_ws_monitor(controller.address, WsMonitorCmd.REMOVE_CONTROLLER)
            await Controller.activate(id)
            send_cmd_to_ws_monitor(controller.address, WsMonitorCmd.ADD_CONTROLLER)
        else:
            await Controller.deactivate(id)
            send_cmd_to_ws_monitor(controller.address, WsMonitorCmd.REMOVE_CONTROLLER)
        return TestControllerMutation(ok=connection_ok)


class ControllerQuery(graphene.ObjectType):
    controllers = graphene.List(lambda: ControllerType)
    controller = graphene.Field(lambda: ControllerType, id=graphene.String())

    @administrator_required
    async def resolve_controllers(self, _info, **kwargs):
        controllers = await Controller.query.gino.all()
        objects = [
            ControllerType(**controller.__values__)
            for controller in controllers
        ]
        return objects

    @administrator_required
    async def resolve_controller(self, _info, id, **kwargs):
        controller = await Controller.query.where(Controller.id == id).gino.first()
        if not controller:
            raise GraphQLError(_('No such controller.'))
        return ControllerType(**controller.__values__)


class ControllerMutations(graphene.ObjectType):
    addController = AddControllerMutation.Field()
    updateController = UpdateControllerMutation.Field()
    removeController = RemoveControllerMutation.Field()
    testController = TestControllerMutation.Field()


controller_schema = graphene.Schema(query=ControllerQuery,
                                    mutation=ControllerMutations,
                                    auto_camelcase=False)
