from starlette.responses import JSONResponse
from starlette.graphql import GraphQLApp as starlette_GraphQLApp
import graphene

from .app import app

import json

class GraphQLApp(starlette_GraphQLApp):

    async def handle_graphql(self, request):
        resp = await super().handle_graphql(request)
        # a sad line
        dic = json.loads(resp.body)
        if dic['errors']:
            del dic['data']
            return JSONResponse(dic)
        return JSONResponse(dic['data'])


class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="stranger"))

    def resolve_hello(self, info, name):
        return "Hello " + name


app.add_route('/', GraphQLApp(schema=graphene.Schema(query=Query)))