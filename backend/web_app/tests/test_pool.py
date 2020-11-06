# -*- coding: utf-8 -*-
import pytest
import uuid
from web_app.tests.utils import VdiHttpTestCase
from tornado.testing import gen_test
from tornado import gen

from common.settings import VEIL_WS_MAX_TIME_TO_WAIT
from web_app.pool.schema import pool_schema
from web_app.tests.utils import execute_scheme
from common.models.pool import Pool

from web_app.tests.fixtures import (fixt_db, fixt_controller, fixt_create_automated_pool, fixt_create_static_pool,  # noqa
                            fixt_auth_context, fixt_group, fixt_user, fixt_user_admin, fixt_user_another_admin, # noqa
                            fixt_launch_workers, fixt_veil_client)  # noqa

pytestmark = [pytest.mark.pools]


# Automated pool
@pytest.mark.asyncio
async def test_create_automated_pool(fixt_launch_workers, fixt_db, fixt_create_automated_pool,  # noqa
                                     fixt_auth_context):  # noqa
    """Create and remove automated pool"""

    # check that pool was successfully created'
    assert fixt_create_automated_pool['is_pool_successfully_created']


@pytest.mark.asyncio
async def test_update_automated_pool(fixt_launch_workers, fixt_db, fixt_create_automated_pool,  # noqa
                                     fixt_auth_context):  # noqa
    """Create automated pool, update this pool, remove this pool"""

    # check that pool was successfully created'
    assert fixt_create_automated_pool['is_pool_successfully_created']

    pool_id = fixt_create_automated_pool['id']

    new_pool_name = 'test_pool_{}'.format(str(uuid.uuid4())[:7])
    qu = """
    mutation {
        updateDynamicPool(
            pool_id: "%s"
            verbose_name: "%s",
            reserve_size: 1,
            total_size: 4,
            keep_vms_on: true){
            ok
        }
    }""" % (pool_id, new_pool_name)
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed['updateDynamicPool']['ok']


@pytest.mark.asyncio
@pytest.mark.usefixtures('fixt_launch_workers', 'fixt_db', 'fixt_user_admin', # noqa
                         'fixt_create_automated_pool', 'fixt_user_another_admin')  # noqa
class PoolTestCase(VdiHttpTestCase):

    @gen_test(timeout=VEIL_WS_MAX_TIME_TO_WAIT + 10)
    def test_automated_pool_expand(self):

        pool = yield Pool.query.gino.first()
        pool_type = yield pool.pool_type
        self.assertEqual(pool_type, Pool.PoolTypes.AUTOMATED)
        pool_id = pool.id

        vms_amount = yield pool.get_vm_amount()
        self.assertEqual(vms_amount, 1)  # Сначала в пуле должна быть 1 VM

        # Авторизуемся, чтобы получить токен
        body = '{"username": "test_user_admin","password": "veil"}'
        response_dict = yield self.get_response(body=body, url='/auth')
        access_token = response_dict['data']['access_token']
        self.assertTrue(access_token)

        # Формируем данные для тестируемого параметра
        headers = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}
        body = '{"remote_protocol": "spice"}'
        url = '/client/pools/{pool_id}/'.format(pool_id=pool_id)

        response_dict = yield self.get_response(body=body, url=url, headers=headers)

        if 'errors' in response_dict:
            # Исключение на случай отсутствия лицензии
            response_data = response_dict['errors'][0]
            response_code = response_data['code']
            self.assertIn(response_code, ['001', '002'])
        else:
            response_data = response_dict['data']
            self.assertIsInstance(response_data, dict)
            self.assertIn('port', response_data)

            # Расширение пула не могло произойти так быстро, поэтому убеждаемся, что нет свободных ВМ.
            # Авторизуемся под вторым админом, чтобы получить токен
            body = '{"username": "test_user_admin2","password": "veil"}'
            response_dict = yield self.get_response(body=body, url='/auth')
            access_token = response_dict['data']['access_token']
            self.assertTrue(access_token)

            # Формируем данные для тестируемого параметра
            headers = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}
            body = '{"remote_protocol": "spice"}'
            url = '/client/pools/{pool_id}/'.format(pool_id=pool_id)

            response_dict = yield self.get_response(body=body, url=url, headers=headers)
            response_data = response_dict['data']
            self.assertIsInstance(response_data, dict)
            # response_message = response_data['message']
            # self.assertEqual('В пуле нет свободных машин', response_message)
            port = response_data['port']
            self.assertEqual(0, port)

            # Ждем время ожидания монитора ресурсов + накладки, чтобы убедиться, что пул расширился
            yield gen.sleep(VEIL_WS_MAX_TIME_TO_WAIT + 5)

            vms_amount = yield pool.get_vm_amount()
            self.assertEqual(2, vms_amount)  # Тут ожидаем, что уже 2


# ----------------------------------------------
# Static pool
@pytest.mark.asyncio
async def test_create_static_pool(fixt_launch_workers, fixt_db, fixt_create_static_pool,  # noqa
                                  fixt_auth_context):  # noqa
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
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
    assert len(executed['pool']['vms']) == 1


@pytest.mark.asyncio
async def test_update_static_pool(fixt_launch_workers, fixt_db, fixt_create_static_pool,  # noqa
                                  fixt_auth_context):  # noqa
    """Create static pool, update this pool, remove this pool"""
    pool_id = fixt_create_static_pool['id']

    new_pool_name = 'test_pool_{}'.format(str(uuid.uuid4())[:7])
    qu = """
    mutation {
        updateStaticPool(pool_id: "%s", verbose_name: "%s", keep_vms_on: true){
         ok
    }
    }""" % (pool_id, new_pool_name)
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed['updateStaticPool']['ok']


@pytest.mark.asyncio
async def test_remove_and_add_vm_in_static_pool(fixt_launch_workers, fixt_db, fixt_controller,  # noqa
                                                fixt_create_static_pool, fixt_auth_context):  # noqa
    """Create automated pool, make request to check data,
    remove a vm from this pool, add the removed vm back to this pool, remove this pool"""
    pool_id = fixt_create_static_pool['id']

    # get pool info
    qu = """{
      pool(pool_id: "%s") {
        pool_type
          vms{
            id
            verbose_name
        }
      }
    }""" % pool_id
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)

    vms_in_pool_list = executed['pool']['vms']
    assert len(vms_in_pool_list) == 1

    # remove first vm from pool
    vm_id = vms_in_pool_list[0]['id']
    vm_verbose_name = vms_in_pool_list[0]['verbose_name']
    qu = '''
      mutation {
        removeVmsFromStaticPool(pool_id: "%s", vm_ids: ["%s"]){
          ok
        }
      }''' % (pool_id, vm_id)
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)

    assert executed['removeVmsFromStaticPool']['ok']

    # add removed machine back to pool
    qu = '''
      mutation {
                addVmsToStaticPool(pool_id: "%s", vms: [{id: "%s", verbose_name: "%s"}]){
                    ok
                  }
                }''' % (pool_id, vm_id, vm_verbose_name)
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed['addVmsToStaticPool']['ok']


@pytest.mark.asyncio
@pytest.mark.usefixtures('fixt_launch_workers', 'fixt_db', 'fixt_controller', 'fixt_group', 'fixt_user',
                         'fixt_create_static_pool')
class TestPoolPermissionsSchema:

    async def test_pool_user_permission(self, snapshot, fixt_auth_context):  # noqa
        pools = await Pool.query.gino.all()
        pool = pools[0]
        query = """mutation{
                            entitleUsersToPool(pool_id: "%s",
                                               users: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                            {
                                ok,
                                pool{users{id}}
                            }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

        query = """mutation{
                    removeUserEntitlementsFromPool(pool_id: "%s",
                                       users: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                    {
                        ok,
                        pool{users{id}}
                    }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_pool_group_permission(self, snapshot, fixt_auth_context):  # noqa
        pools = await Pool.query.gino.all()
        pool = pools[0]
        query = """mutation{
                                    addPoolGroup(pool_id: "%s",
                                                 groups: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                                    {
                                        ok,
                                        pool{assigned_groups{id}, possible_groups{id}}
                                    }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

        query = """mutation{
                            removePoolGroup(pool_id: "%s",
                                            groups: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                            {
                                ok,
                                pool{assigned_groups{id}, possible_groups{id}}
                            }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_pool_role_permission(self, snapshot, fixt_auth_context):  # noqa
        pools = await Pool.query.gino.all()
        pool = pools[0]
        query = """mutation{
                            addPoolRole(pool_id: "%s",
                                        roles: [ADMINISTRATOR])
                            {
                                ok,
                                pool{assigned_roles, possible_roles}
                            }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

        query = """mutation{
                            removePoolRole(pool_id: "%s",
                                        roles: [OPERATOR])
                            {
                                ok,
                                pool{assigned_roles, possible_roles}
                            }}""" % pool.id

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)


@pytest.mark.asyncio
async def test_pools_ordering(fixt_launch_workers,  fixt_db, fixt_controller, fixt_create_automated_pool,  # noqa
                              fixt_auth_context):  # noqa

    # list = ["verbose_name", "cluster_id", "node_id", "status", "controller", "controller_address", "users_count",
    #        "vms_count", "pool_type"]
    list = ["verbose_name", "controller_address", "users_count", "vm_amount", "pool_type"]
    for ordering in list:
        qu = """
                {
                  pools(ordering: "%s") {
                    pool_id
                    controller {
                      id
                      verbose_name
                      address
                    }
                    status
                    verbose_name
                    pool_type
                    cluster_id
                    node_id
                    template_id
                    datapool_id
                    initial_size
                    os_type
                    assigned_groups {
                      id
                      verbose_name
                    }
                    possible_groups {
                      id
                      verbose_name
                    }
                    assigned_roles
                    possible_roles
                    assigned_connection_types
                    possible_connection_types
                 }
                }
            """ % ordering

        await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
