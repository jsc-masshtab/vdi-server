

from graphql import GraphQLObjectType, GraphQLSchema, graphql, is_type

import graphene

class Sub2Type(graphene.ObjectType):
    a = b = c = graphene.String()

    async def resolve_a(self, info):
        return ";"

    resolve_b = resolve_c = resolve_a


class Sub1Type(graphene.ObjectType):
    sub2 = graphene.Field(lambda: Sub2Type, some=graphene.Int(), arg=graphene.Int())
    the = rest = of = it = graphene.String()

    async def resolve_sub2(self, info, some, arg):
        return Sub2Type()

    async def _resolve(self, info):
        return '.'

    resolve_the = resolve_rest = resolve_of = resolve_it = _resolve


class RootType(graphene.ObjectType):
    sub1 = graphene.Field(lambda: Sub1Type)

    async def resolve_sub1(self, info):
        return Sub1Type()



class Mut(graphene.Mutation):
    #
    # development only ?
    #
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()

    def mutate(self, info, id):
        return Mut(ok=True)


class RootQuery(graphene.ObjectType):
    root = graphene.Field(lambda: RootType, id=graphene.Int(), info=graphene.String())

    async def resolve_root(self, _info, id, info):
        return RootType()


class RootMutations(graphene.ObjectType):
    mut = Mut.Field()


schema = graphene.Schema(query=RootQuery, mutation=RootMutations, auto_camelcase=False)

from graphql.graphql import execute_graphql, graphql

with open('/home/pwtail/projects/vdiserver/dev/bench/settings.py') as f:
    text = f.read()

mod = {}
exec(text, mod)

from graphql.execution.executors.asyncio import AsyncioExecutor

async def exec():
    r = await graphql(schema, mod['query'], executor=AsyncioExecutor(), return_promise=True)
    return r