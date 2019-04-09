
import pytest

from vdi.graphql import schema

@pytest.fixture
async def db():
    from vdi.db import db
    await db.init()
    return db


@pytest.fixture
async def image_name():
    from vdi import prepare
    await prepare.main()
    return 'image.qcow2'


@pytest.fixture
async def template_vm(db, image_name):
    qu = '''
    mutation {
      createTemplate(image_name: "%(image_name)s") {
        template {
            id
        }
      }
    }
    ''' % locals()
    r = await schema.exec(qu)
    id = r.data['createTemplate']['template']['id']
    yield id
    qu = '''
    mutation {
      dropTemplate(id: "%(id)s") {
        ok
      }
    }
    ''' % locals()
    await exec(qu)


@pytest.fixture
def pool_name():
    import random, string
    uid = ''.join(
        random.choice(string.ascii_letters) for _ in range(3)
    )
    return f"pool-{uid}"


@pytest.fixture
async def pool(template_vm, pool_name):
    qu = '''
    mutation {
      addPool(name: "%(pool_name)s", template_id: %(template_vm)s) {
        id
      }
    }
    ''' % locals()
    r = await schema.exec(qu)
    id = r.data['addPool']['id']
    yield {
        'id': id,
        'name': r.data['addPool']['name'],
    }
    qu = '''
        mutation {
          dropTemplate(id: "%(id)s") {
            ok
          }
        }
        ''' % locals()
    await exec(qu)
