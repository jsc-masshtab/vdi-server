import graphene
from controller.models import Controller
from controller.models import ControllerUserType


ControllerUserTypeGr = graphene.Enum.from_enum(ControllerUserType)


class ControllerType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    status = graphene.String()
    address = graphene.String()
    description = graphene.String()
    version = graphene.String()
    default = graphene.Boolean()

    controller_user_type = ControllerUserTypeGr()
    user_login = graphene.String()
    user_password = graphene.String()

    async def resolve_status(self, _info):
        return self.get_status()

    async def get_status(self):
        # if not self.status:
        #     try:
        #         await CheckController(controller_ip=self.address)
        #         self.status = 'ACTIVE'
        #     except (HTTPClientError, NotFound, OSError):
        #         self.status = 'FAILED'
        return self.status


class AddController(graphene.Mutation):
    class Arguments:
        verbose_name = graphene.String(required=True)
        address = graphene.String(required=True)

        controller_user_type = ControllerUserTypeGr(required=True)
        user_login = graphene.String(required=True)
        user_password = graphene.String(required=True)

        description = graphene.String()
        default = graphene.Boolean()

    ok = graphene.Boolean()

    async def mutate(self, _info, verbose_name, address, controller_user_type, user_login, user_password,
                     description=None, default=False):
        # TODO: validation
        # check that its possible to log in with given credentials (auth request to controller)

        # TODO: add token and credentials
        controller = await Controller.create(
            verbose_name=verbose_name,
            address=address,
            description=description,
            default=default,
            controller_user_type=ControllerUserType(controller_user_type).name,
            user_login=user_login,
            user_password=user_password
        )

        # add controller to resources_monitor_manager
        # resources_monitor_manager.add_controller(ip)
        return AddController(ok=True)


class RemoveController(graphene.Mutation):
    class Arguments:
        id = graphene.String()

    ok = graphene.Boolean()

    async def mutate(self, info, id):
        # TODO: validation (if exist)
        # TODO: remove connected pools
        status = await Controller.delete.where(Controller.id == id).gino.status()
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
        # TODO: validation
        controller = await Controller.query.where(Controller.id == id).gino.first()
        return ControllerType(**controller.__values__)


class ControllerMutations(graphene.ObjectType):
    addController = AddController.Field()
    removeController = RemoveController.Field()


controller_schema = graphene.Schema(query=ControllerQuery,
                                    mutation=ControllerMutations,
                                    auto_camelcase=False)
