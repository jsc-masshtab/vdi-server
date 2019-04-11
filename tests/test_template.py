import pytest


from vdi.graphql.schema import exec

from vdi.fixtures import db, image_name

@pytest.mark.asyncio
async def test_create_drop_template(db, image_name):
    qu = '''
    mutation {
      createTemplate(image_name: "%(image_name)s") {
        template {
            id
        }
      }
    }
    ''' % locals()
    r = await exec(qu)
    id = r['createTemplate']['template']['id']
    qu = '''
    mutation {
      dropTemplate(id: "%(id)s") {
        ok
      }
    }
    ''' % locals()
    r = await exec(qu)
    assert r['dropTemplate']['ok']


