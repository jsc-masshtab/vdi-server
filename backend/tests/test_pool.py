from async_generator import async_generator, yield_, asynccontextmanager

from fixtures.fixtures import (
    fixt_db, image_name, create_template, create_pool, pool_name, pool_settings as fixture_pool_settings,
    conn, fixt_create_static_pool
)

from vdi.graphql_api.pool import RemovePool
from vdi.graphql_api.pool import DesktopPoolType
from vdi.graphql_api import schema

from db.db import db


import pytest
import json

import asyncio


@pytest.fixture
def pool_settings(fixture_pool_settings):
    vars = dict(fixture_pool_settings)
    vars['settings']['initial_size'] = 1
    return vars


@pytest.mark.asyncio
async def test_create_pool(create_pool, pool_settings):
    id = create_pool['id']

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


@pytest.mark.asyncio
async def test_remove_pool(create_pool, pool_settings):
    pass


@pytest.mark.asyncio
async def test_pools_list(create_pool, pool_settings):
    qu = """{
      pools {
        id
        settings {
          initial_size
          reserve_size
        }
      }
    }""" % locals()
    r = await schema.exec(qu)
    for p in r['pools']:
        assert p['settings']['initial_size']
        assert p['settings']['reserve_size']


#@pytest.mark.asyncio
#async def test_wake_pool(create_pool, pool_settings, conn):
#    pool_id = create_pool['id']
#    ins = await Pool.get_pool(pool_id)
#    vms = await ins.load_vms(conn)
#    Pool.instances.pop(pool_id)
#    ins = await Pool.wake_pool(pool_id)
#    new_vms = await ins.load_vms(conn)
#    assert new_vms == vms


@pytest.mark.asyncio
async def test_create_static_pool(fixt_create_static_pool):
    #
    pool_id = fixt_create_static_pool['id']

    # get pool info
    qu = """{
      pool(id: %i) {
        desktop_pool_type
          vms{
            name
        }
      }
    }""" % pool_id
    res = await schema.exec(qu)

    li = res['pool']['vms']
    assert len(li) == 2
    assert res['pool']['desktop_pool_type'] == DesktopPoolType.STATIC.name


@pytest.mark.asyncio
async def test_remove_and_add_vm_in_static_pool(fixt_create_static_pool):

    pool_id = fixt_create_static_pool['id']
    vms_in_pool_list = fixt_create_static_pool['vms']
    assert len(vms_in_pool_list) == 2

    # remove first vm from pool
    vm_id = vms_in_pool_list[0]['id']
    qu = '''
      mutation {
        removeVmsFromStaticPool(pool_id: %i, vm_ids: ["%s"]){
          ok
        }
      }''' % (pool_id, vm_id)
    res = await schema.exec(qu)
    assert res['removeVmsFromStaticPool']['ok']

    # add removed machine back to pool
    qu = '''
      mutation {
        addVmsToStaticPool(pool_id: %i, vm_ids: ["%s"]){
          ok
        }
      }''' % (pool_id, vm_id)
    res = await schema.exec(qu)
    assert res['addVmsToStaticPool']['ok']


