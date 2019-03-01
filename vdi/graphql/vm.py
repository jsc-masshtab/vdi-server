
from asyncpg.connection import Connection

import json
import graphene

from starlette.graphql import GraphQLApp

from cached_property import cached_property as cached

from ..app import app
from ..db import db
from ..tasks import vm

class CreateTemplate(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        name = graphene.String()

    id = graphene.String()

    @db.connect()
    async def mutate(self, info, name, conn: Connection):
        domain = await vm.SetupDomain(image_name=name)
        qu = '''
        INSERT INTO vm (id, is_template) VALUES ($1, $2)
        ''', domain['id'], True
        await conn.fetch(*qu)
        return CreateTemplate(id=domain['id'])


# TODO create template vm


class VmMutations(graphene.ObjectType):
    createTemplate = CreateTemplate.Field()

def get_selections(info):
    return [
        f.name.value
        for f in info.field_asts[0].selection_set.selections
    ]


class VmQuery(graphene.ObjectType):
    pass


from graphql.execution.executors.asyncio import AsyncioExecutor

schema = graphene.Schema(#query=VmQuery,
                         mutation=VmMutations, auto_camelcase=False)

app.add_route('/vm', GraphQLApp(schema, executor_class=AsyncioExecutor))




