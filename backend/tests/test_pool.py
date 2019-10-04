import pytest

from fixtures.fixtures import (
    fixt_db, fixt_create_static_pool, fixt_create_automated_pool,
    conn, get_resources_for_automated_pool
)

from vdi.graphql_api.pool import DesktopPoolType
from vdi.graphql_api import schema

from vdi.tasks import vm


@pytest.mark.asyncio
async def test_create_automated_pool(fixt_create_automated_pool):
    pool_id = fixt_create_automated_pool['id']

    qu = """{
      pool(id: %i) {
        desktop_pool_type
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
    }""" % pool_id
    res = await schema.exec(qu)
    assert res['pool']['settings']['initial_size'] == 1
    assert res['pool']['desktop_pool_type'] == DesktopPoolType.AUTOMATED.name


@pytest.mark.asyncio
async def test_change_total_size_of_autopool(fixt_create_automated_pool):
    pool_id = fixt_create_automated_pool['id']


@pytest.mark.asyncio
async def test_copy_domain():
    resources = await get_resources_for_automated_pool()
    #print('resources', resources)
    params = {
        'verbose_name': "a_name_for_template",
        'name_template': 'vm_name_template',
        'domain_id': resources['template_id'],
        'datapool_id': resources['datapool_id'],
        'controller_ip': resources['controller_ip'],
        'node_id': resources['node_id'],
    }
    vm_data = await vm.CopyDomain(**params).task
    print('vm_data', vm_data)


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
async def test_change_pool_name(fixt_create_static_pool):
    pool_id = fixt_create_static_pool['id']

    # change name
    qu = """
    mutation {
      changePoolName(new_name: "New_pool_name", pool_id: %i){
        ok
      }
    }""" % pool_id
    await schema.exec(qu)


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


