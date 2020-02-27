# -*- coding: utf-8 -*-
import pytest
import uuid

from pool.schema import pool_schema
from tests.utils import execute_scheme
from pool.models import Pool

from tests.fixtures import (fixt_db, fixt_create_automated_pool, fixt_create_static_pool, fixt_entitle_user_to_pool,  # noqa
                            auth_context_fixture, fixt_controller, fixt_group, fixt_user)  # noqa

pytestmark = [pytest.mark.pools]


# ----------------------------------------------
# Automated pool
@pytest.mark.asyncio
async def test_create_automated_pool(fixt_db, fixt_controller, fixt_create_automated_pool, auth_context_fixture):  # noqa
    """Create automated pool, make request to check data, remove this pool"""
    pool_id = fixt_create_automated_pool['id']

    # check that pool was successfully created'
    assert fixt_create_automated_pool['is_pool_successfully_created']

    qu = """{
      pool(pool_id: "%s") {
        pool_type,
        initial_size
      }
    }""" % pool_id
    executed = await execute_scheme(pool_schema, qu, context=auth_context_fixture)
    assert executed['pool']['initial_size'] == 1


@pytest.mark.asyncio
async def test_update_automated_pool(fixt_db, fixt_controller, fixt_create_automated_pool, auth_context_fixture):  # noqa
    """Create automated pool, update this pool, remove this pool"""
    pool_id = fixt_create_automated_pool['id']

    # check that pool was successfully created'
    assert fixt_create_automated_pool['is_pool_successfully_created']

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
    executed = await execute_scheme(pool_schema, qu, context=auth_context_fixture)
    assert executed['updateDynamicPool']['ok']


# ----------------------------------------------
# Static pool
@pytest.mark.asyncio
async def test_create_static_pool(fixt_db, fixt_controller, fixt_create_static_pool, auth_context_fixture):  # noqa
    """Create static pool, make request to check data, remove this pool"""
    pool_id = fixt_create_static_pool['id']
    assert fixt_create_static_pool['ok']

    # get pool info
    qu = """{
      pool(pool_id: "%s") {
        pool_type
          vms{
            verbose_name
        }
      }
    }""" % pool_id
    executed = await execute_scheme(pool_schema, qu, context=auth_context_fixture)  # noqa


@pytest.mark.asyncio
async def test_update_static_pool(fixt_db, fixt_controller, fixt_create_static_pool, auth_context_fixture):  # noqa
    """Create static pool, update this pool, remove this pool"""
    pool_id = fixt_create_static_pool['id']

    new_pool_name = 'test_pool_{}'.format(str(uuid.uuid4())[:7])
    qu = """
    mutation {
        updateStaticPool(pool_id: "%s", verbose_name: "%s", keep_vms_on: true){
         ok
    }
    }""" % (pool_id, new_pool_name)
    executed = await execute_scheme(pool_schema, qu, context=auth_context_fixture)
    assert executed['updateStaticPool']['ok']


@pytest.mark.asyncio
async def test_remove_and_add_vm_in_static_pool(fixt_db, fixt_controller, fixt_create_static_pool, auth_context_fixture):  # noqa
    """Create automated pool, make request to check data,
    remove a vm from this pool, add the removed vm back to this pool, remove this pool"""
    pool_id = fixt_create_static_pool['id']

    # get pool info
    qu = """{
      pool(pool_id: "%s") {
        pool_type
          vms{
            id
        }
      }
    }""" % pool_id
    executed = await execute_scheme(pool_schema, qu, context=auth_context_fixture)
    vms_in_pool_list = executed['pool']['vms']
    assert len(vms_in_pool_list) == 1

    # remove first vm from pool
    vm_id = vms_in_pool_list[0]['id']
    qu = '''
      mutation {
        removeVmsFromStaticPool(pool_id: "%s", vm_ids: ["%s"]){
          ok
        }
      }''' % (pool_id, vm_id)
    executed = await execute_scheme(pool_schema, qu, context=auth_context_fixture)
    assert executed['removeVmsFromStaticPool']['ok']

    # add removed machine back to pool
    qu = '''
      mutation {
        addVmsToStaticPool(pool_id: "%s", vm_ids: ["%s"]){
          ok
        }
      }''' % (pool_id, vm_id)
    executed = await execute_scheme(pool_schema, qu, context=auth_context_fixture)
    assert executed['addVmsToStaticPool']['ok']


@pytest.mark.asyncio
@pytest.mark.usefixtures('fixt_db', 'fixt_controller', 'fixt_group', 'fixt_user', 'fixt_create_static_pool')
class TestPoolPermissionsSchema:

    async def test_pool_user_permission(self, snapshot, auth_context_fixture):  # noqa
        pools = await Pool.query.gino.all()
        pool = pools[0]
        query = """mutation{
                            entitleUsersToPool(pool_id: "%s",
                                               users: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                            {
                                ok,
                                pool{users{id}}
                            }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

        query = """mutation{
                    removeUserEntitlementsFromPool(pool_id: "%s",
                                       users: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                    {
                        ok,
                        pool{users{id}}
                    }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_pool_group_permission(self, snapshot, auth_context_fixture):  # noqa
        pools = await Pool.query.gino.all()
        pool = pools[0]
        query = """mutation{
                                    addPoolGroup(pool_id: "%s",
                                                 groups: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                                    {
                                        ok,
                                        pool{assigned_groups{id}, possible_groups{id}}
                                    }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

        query = """mutation{
                            removePoolGroup(pool_id: "%s",
                                            groups: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                            {
                                ok,
                                pool{assigned_groups{id}, possible_groups{id}}
                            }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_pool_role_permission(self, snapshot, auth_context_fixture):  # noqa
        pools = await Pool.query.gino.all()
        pool = pools[0]
        query = """mutation{
                            addPoolRole(pool_id: "%s",
                                        roles: [VM_ADMINISTRATOR, READ_ONLY])
                            {
                                ok,
                                pool{assigned_roles, possible_roles}
                            }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

        query = """mutation{
                            removePoolRole(pool_id: "%s",
                                        roles: [READ_ONLY])
                            {
                                ok,
                                pool{assigned_roles, possible_roles}
                            }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)
