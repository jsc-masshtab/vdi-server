
from vdi.fixtures import db, image_name, template_vm, pool, pool_name
from vdi.graphql import schema
import pytest

import asyncio


@pytest.fixture
def query_addPool(template_vm, pool_name):
    return '''
    mutation {
      addPool(name: "%(pool_name)s", template_id: "%(template_vm)s", block: true, settings: {initial_size: 1}) {
        id
      }
    }
    ''' % locals()


@pytest.mark.asyncio
async def test_create_pool(pool, query_addPool):
    id = pool['id']

    qu = """{
      pool(id: %(id)s) {
        settings {
          initial_size
        }
        state {
          running
          available {
            id
          }
        }
      }
    }""" % locals()
    r = await schema.exec(qu)
    assert r['pool']['settings']['initial_size'] == 1
    li = r['pool']['state']['available']
    assert len(li) == 1
