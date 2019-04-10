import graphene
import json

from asyncpg.connection import Connection

from ..db import db
from ..tasks import vm, admin

from .util import get_selections

class TemplateType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    info = graphene.String()


class CreateTemplate(graphene.Mutation):
    '''
    Awaits the result. Mostly for development use
    '''
    class Arguments:
        name = graphene.String()
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
        t = TemplateType(id=domain['id'], info=veil_info, name=domain['verbose_name'])
        return CreateTemplate(template=t)


class DropTemplate(graphene.Mutation):
    class Arguments:
        id = graphene.String()

    ok = graphene.Boolean()

    @db.connect()
    async def mutate(self, info, id, conn: Connection):
        await vm.DropDomain(id=id)
        qu = "DELETE from template_vm WHERE id = $1", id
        await conn.fetch(*qu)
        return DropTemplate(ok=True)



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

        fields = []
        for s in selections:
            if s == 'info':
                fields.append('veil_info')
            elif s == 'name' and 'veil_info' not in fields:
                fields.append('veil_info')
            else:
                fields.append(s)

        qu = f"SELECT {', '.join(fields)} FROM template_vm"
        data = await conn.fetch(qu)

        templates = [
            dict(zip(fields, t)) for t in data
        ]

        def make_template(t):
            if 'veil_info' in t:
                t['info'] = t.pop('veil_info')

            if 'name' in selections:
                info = json.loads(t['info'])
                t['name'] = info['verbose_name']
            if 'info' not in selections:
                t.pop('info', None)
            return TemplateType(**t)

        return [
            make_template(t) for t in templates
        ]


