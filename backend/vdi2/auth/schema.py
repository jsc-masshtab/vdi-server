import graphene
from auth.models import User


class UserType(graphene.ObjectType):
    username = graphene.String()
    password = graphene.String()
    email = graphene.String()


class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    ok = graphene.Boolean()

    async def mutate(self, info, username, password, email):
        await User.create_user(username, password, email)
        return {'ok': True}


class UserQuery(graphene.ObjectType):
    users = graphene.List(lambda: UserType)
    user = graphene.Field(lambda: UserType, username=graphene.String())

    async def resolve_users(self, info):
        users = await User.query.gino.all()
        objects = [
            UserType(**user.__values__)
            for user in users
        ]
        return objects

    async def resolve_user(self, info, username):
        # TODO: validation
        user = await User.query.where(User.username == username).gino.first()
        return UserType(**user.__values__)


class UserMutations(graphene.ObjectType):
    CreateUser = CreateUser.Field()


user_schema = graphene.Schema(mutation=UserMutations,
                              query=UserQuery,
                              auto_camelcase=False)
