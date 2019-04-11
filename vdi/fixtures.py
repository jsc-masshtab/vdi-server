
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
    yield 'image.qcow2'
    print('image destroy')


@pytest.fixture
async def template_vm(db, image_name):
    print('createTemplate')
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
    id = r['createTemplate']['template']['id']
    yield id
    print('destroy vm')
    qu = '''
    mutation {
      dropTemplate(id: "%(id)s") {
        ok
      }
    }
    ''' % locals()
    await schema.exec(qu)


@pytest.fixture
def pool_name():
    import random, string
    uid = ''.join(
        random.choice(string.ascii_letters) for _ in range(3)
    )
    return f"pool-{uid}"

@pytest.fixture
def query_addPool(pool_name):
    return '''
    mutation {
      addPool(name: "%(pool_name)s", template_id: %(template_vm)s, block: true) {
        id
      }
    }
    '''


@pytest.fixture
async def pool(template_vm, query_addPool):
    print('addPool')
    r = await schema.exec(query_addPool)
    id = r['addPool']['id']
    yield {
        'id': id,
    }
    print('destroy pool')
    qu = '''
    mutation {
      removePool(id: %(id)s) {
        ok
      }
    }
    ''' % locals()
    await schema.exec(qu)

