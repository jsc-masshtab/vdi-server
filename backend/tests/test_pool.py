import pytest
import uuid

from pool.schema import pool_schema

from tests.utils import execute_scheme


# ----------------------------------------------
# Automated pool
@pytest.mark.asyncio
async def test_create_automated_pool(fixt_db, fixt_create_automated_pool):
    pool_id = fixt_create_automated_pool['id']
    print('pool_id_', pool_id)
    qu = """{
      pool(pool_id: "%s") {
        pool_type,
        initial_size
      }
    }""" % pool_id
    executed = await execute_scheme(pool_schema, qu)
    assert executed['pool']['initial_size'] == 1


@pytest.mark.asyncio
async def test_update_automated_pool(fixt_db, fixt_create_automated_pool):
    pool_id = fixt_create_automated_pool['id']

    new_pool_name = 'test_pool_{}'.format(str(uuid.uuid4())[:7])
    qu = """
    mutation {
        updateDynamicPool(
            pool_id: "%s"
            verbose_name: "%s",
            reserve_size: 1,
            total_size: 5,
            keep_vms_on: true){
            ok
        }
    }""" % (pool_id, new_pool_name)
    executed = await execute_scheme(pool_schema, qu)
    assert executed['updateDynamicPool']['ok']


# ----------------------------------------------
# Static pool
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
