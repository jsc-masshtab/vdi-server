import graphene
from controller.models import Controller


class ControllerType(graphene.ObjectType):
    id = graphene.String()
    verbose_name = graphene.String()
    status = graphene.String()
    address = graphene.String()
    description = graphene.String()
    version = graphene.String()
    default = graphene.Boolean()


class AddController(graphene.Mutation):
    class Arguments:
        verbose_name = graphene.String(required=True)
        address = graphene.String(required=True)
        description = graphene.String()
        default = graphene.Boolean()

    ok = graphene.Boolean()

    async def mutate(self, info, verbose_name, address, description=None, default=False):
        # TODO: validation
        # TODO: add token and credentials
        controller = await Controller.create(
            verbose_name=verbose_name,
            address=address,
            description=description,
            default=default
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

    async def resolve_controllers(self, info):
        controllers = await Controller.query.gino.all()
        objects = [
            ControllerType(**controller.__values__)
            for controller in controllers
        ]
        return objects

    async def resolve_controller(self, info, id):
        # TODO: validation
        controller = await Controller.query.where(Controller.id == id).gino.first()
        return ControllerType(**controller.__values__)


class ControllerMutations(graphene.ObjectType):
    addController = AddController.Field()
    removeController = RemoveController.Field()


controller_schema = graphene.Schema(query=ControllerQuery,
                                    mutation=ControllerMutations,
                                    auto_camelcase=False)
