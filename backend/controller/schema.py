# -*- coding: utf-8 -*-
import graphene
from graphql import GraphQLError

from common.veil_decorators import superuser_required
from common.veil_errors import SimpleError

from database import StatusGraphene
from auth.utils import crypto
from controller.client import ControllerClient
from controller.models import Controller
from resources_monitoring.resources_monitor_manager import resources_monitor_manager

from languages import lang_init
from journal.journal import Log as log


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

    @superuser_required
    async def mutate(self, _info, verbose_name, address, username,
                     password, ldap_connection, description=None):
        try:
            if len(verbose_name) < 1:
                raise SimpleError(_('Controller name cannot be empty.'))
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
            msg = _('Successfully added new controller {name} with address {address}.').format(
                name=controller.verbose_name,
                address=address)
            await log.info(msg)
            return AddControllerMutation(ok=True, controller=ControllerType(**controller.__values__))
        except SimpleError as E:
            raise SimpleError(E)
        except Exception as E:
            msg = _('Add new controller with address {address}: operation failed.').format(address=address)
            descr = str(E)
            raise SimpleError(msg, description=descr)


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

    @superuser_required
    async def mutate(self, _info, id, verbose_name=None, address=None, username=None,
                     password=None, ldap_connection=None, description=None):

        # TODO: это нужно перенести в валидатор
        controller = await Controller.get(id)
        if not controller:
            raise SimpleError(_('No such controller.'))

        try:
            await controller.soft_update(verbose_name=verbose_name,
                                         address=address,
                                         description=description,
                                         username=username,
                                         password=password,
                                         ldap_connection=ldap_connection)

            # Берем актуальный адрес контроллера, даже если он уже был изменен
            controller = await Controller.get(id)
            # Переподключаем монитор ресурсов
            await resources_monitor_manager.remove_controller(controller.address)
            await resources_monitor_manager.add_controller(controller.address)
        except Exception as E:
            msg = _('Fail to update controller {id}: {error}').format(
                id=id, error=E)
            # log.error(msg)
            # При редактировании с контроллером произошла ошибка - нужно остановить монитор ресурсов.
            await resources_monitor_manager.remove_controller(controller.address)
            # И деактивировать контроллер
            await Controller.deactivate(id)
            raise SimpleError(msg)

        msg = _('Successfully update controller {name} with address {address}.').format(
            name=controller.verbose_name,
            address=controller.address)
        log.info(msg)
        # На случай, если контроллер был не активен - активируем его.
        await Controller.activate(id)
        return UpdateControllerMutation(ok=True, controller=ControllerType(**controller.__values__))


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
            raise GraphQLError(_('No such controller.'))

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


class TestControllerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @superuser_required
    async def mutate(self, _info, id):
        controller = await Controller.get(id)
        if not controller:
            raise GraphQLError(_('No such controller.'))
        connection_ok = await controller.check_credentials()
        if connection_ok:
            await Controller.activate(id)
            await resources_monitor_manager.remove_controller(controller.address)
            await resources_monitor_manager.add_controller(controller.address)
        else:
            await Controller.deactivate(id)
            await resources_monitor_manager.remove_controller(controller.address)
        return TestControllerMutation(ok=connection_ok)


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
