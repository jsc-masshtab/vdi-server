
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
    yield 'image'
    print('image destroy')


@pytest.fixture
async def create_template(db, image_name):
    qu = '''
    mutation {
      createTemplate(image_name: "%(image_name)s") {
        poolwizard {
          reserve_size
          initial_size
          datapool_id
          node_id
          cluster_id
          controller_ip
          template_id
        }
      }
    }
    ''' % locals()
    r = await schema.exec(qu)
    poolwizard = r['createTemplate']['poolwizard']
    yield poolwizard
    print('destroy vm')
    qu = '''
    mutation {
      dropTemplate(id: "%(template_id)s") {
        ok
      }
    }
    ''' % poolwizard
    await schema.exec(qu)


@pytest.fixture
async def pool_settings(create_template):
    return {
        'settings': create_template,
    }



@pytest.fixture
def pool_name():
    import random, string
    uid = ''.join(
        random.choice(string.ascii_letters) for _ in range(3)
    )
    return f"pool-{uid}"



@pytest.fixture
async def create_pool(create_template, pool_name, pool_settings):
    r = await schema.exec('''
        mutation($settings: PoolSettingsInput) {
          addPool(name: "%(pool_name)s", settings: $settings, block: true) {
            id
          }
        }
        ''' % locals(), pool_settings)
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

