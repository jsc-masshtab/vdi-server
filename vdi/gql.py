from starlette.responses import JSONResponse
from starlette.graphql import GraphQLApp # as starlette_GraphQLApp
import graphene

from .app import app

import json

# class GraphQLApp(starlette_GraphQLApp):
#
#     async def handle_graphql(self, request):
#         resp = await super().handle_graphql(request)
#         # a sad line
#         dic = json.loads(resp.body)
#         if dic['errors']:
#             del dic['data']
#             return JSONResponse(dic)
#         return JSONResponse(dic['data'])

import graphene

class AddPool(graphene.Mutation):
    class Arguments:
        vm_id = graphene.String()

    ok = graphene.Boolean()
    pool = graphene.Field(lambda: PoolType)

    def mutate(self, info, vm_id):
        s = '''
        INSERT INTO pool values (?)
        ''', vm_id
        ok = True
        return AddPool(person=person, ok=ok)


class PoolMutations(graphene.ObjectType):
    add = AddPool.Field()


class PoolType(graphene.ObjectType):
    vm_id = graphene.String()
    name = graphene.String()

    def resolve_vm_id(self, info):
        return 1



class Pool(graphene.ObjectType):
    list = graphene.List(PoolType)

    def resolve_list(self, info):
        return []


# class P


app.add_route('/', GraphQLApp(schema=graphene.Schema(query=Pool, mutation=PoolMutations)))