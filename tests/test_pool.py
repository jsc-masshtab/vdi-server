
from vdi.fixtures import db, image_name, template_vm
from vdi.graphql import schema
import pytest

import asyncio


@pytest.mark.asyncio
async def test_create_pool(template_vm):
    qu = '''
    mutation {
      addPool(name: "my-pool", template_id: "%(template_vm)s") {
        id
      }
    }
    ''' % locals()
    r = await schema.exec(qu)
    id = r.data['addPool']['id']

    async def counter(n):
        for i in range(n):
            await asyncio.sleep(1)
            yield i + 1

    t = 0
    dt = 2
    while t < 20:
        qu = """{
          pool(id: %(id)s) {
            state {
              running
              available {
                id
              }
            }
          }
        }""" % locals()
        r = await schema.exec(qu)
        li = r.data['pool']['state']['available']
        if len(li) == 2:
            return
        # FIXME
        await asyncio.sleep(dt)
        t += dt

    print(f'^^^^ {len(li)}')
    assert False