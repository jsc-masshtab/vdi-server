import graphene
import json

from asyncpg.connection import Connection

from ..db import db
from ..tasks import vm, admin

from .util import get_selections

class TemplateType(graphene.ObjectType):
    id = graphene.String()
    info = graphene.String()


class CreateTemplate(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        image_name = graphene.String()

    template = graphene.Field(TemplateType)

    @db.connect()
    async def mutate(self, info, image_name, conn: Connection):
        domain = await vm.SetupDomain(image_name=image_name)
        veil_info = json.dumps(domain)
        qu = '''
            INSERT INTO template_vm (id, veil_info) VALUES ($1, $2)
            ''', domain['id'], veil_info
        await conn.fetch(*qu)
        t = TemplateType(id=domain['id'], info=veil_info)
        return CreateTemplate(template=t)


class DropTemplate(graphene.Mutation):

    class Arguments:
        id: graphene.String()

    @db.connect()
    async def mutate(self, info, id, conn: Connection):
        await admin.DropDomain(id=id)
        qu = "DROP from template_vm WHERE id = $1", id
        await conn.fetch(*qu)



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




class TemplateMixin:

    templates = graphene.List(TemplateType)

    @db.connect()
    async def resolve_templates(self, info, conn: Connection):
        selections = get_selections(info)
        fields = selections[:]
        if 'info' in selections:
            fields[fields.index('info')] = 'veil_info'
        qu = f"SELECT {', '.join(fields)} FROM template_vm"
        templates = await conn.fetch(qu)
        li = []
        for t in templates:
            t = dict(zip(selections, t))
            li.append(TemplateType(**t))
        return li