import graphene

from asyncpg.connection import Connection

from ..db import db
from ..tasks import vm



class CreateTemplate(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        image_name = graphene.String()

    id = graphene.String()

    @db.connect()
    async def mutate(self, info, image_name, conn: Connection):
        domain = await vm.SetupDomain(image_name=image_name)
        qu = '''
            INSERT INTO template_vm (id) VALUES ($1)
            ''', domain['id']
        await conn.fetch(*qu)
        return CreateTemplate(id=domain['id'])


class AddTemplate(graphene.Mutation):
    class Arguments:
        id = graphene.String()

    ok = graphene.Boolean()

    @db.connect()
    async def mutate(self, info, id, conn: Connection):
        qu = '''
            INSERT INTO template_vm (id) VALUES ($1)
            ''', id
        await conn.fetch(*qu)
        return AddTemplate(ok=True)




