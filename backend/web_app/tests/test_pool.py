# -*- coding: utf-8 -*-
import pytest
import uuid
from web_app.tests.utils import VdiHttpTestCase
from tornado.testing import gen_test
from tornado import gen

from common.settings import VEIL_WS_MAX_TIME_TO_WAIT, PAM_AUTH
from web_app.pool.schema import pool_schema
from web_app.tests.utils import execute_scheme, ExecError
from common.models.pool import Pool
from common.models.task import TaskStatus, Task
from common.veil.veil_gino import Status
from common.veil.veil_redis import wait_for_task_result

from common.models.vm import Vm


from web_app.tests.fixtures import (
    fixt_db,
    fixt_redis_client,
    fixt_controller,
    fixt_create_automated_pool,  # noqa
    fixt_create_static_pool,
    fixt_create_rds_pool,
    fixt_auth_context,
    fixt_group,  # noqa
    fixt_user,
    fixt_user_admin,
    fixt_user_another_admin,  # noqa
    fixt_veil_client,
)  # noqa

pytestmark = [
    pytest.mark.pools,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


# Automated pool
@pytest.mark.asyncio
async def test_create_and_expand_automated_pool(
    fixt_redis_client, fixt_db, fixt_create_automated_pool, fixt_auth_context  # noqa
):  # noqa
    """Create, expand and remove automated pool"""

    # check that pool was successfully created'
    assert fixt_create_automated_pool["is_pool_successfully_created"]

    # launch expand pool task
    pool_id = fixt_create_automated_pool["id"]
    qu = (
        """
    mutation {
        expandPool(pool_id: "%s"){
            ok
            task_id
        }
    }"""
        % pool_id
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["expandPool"]["ok"]

    # wait for expand pool result
    task_id = executed["expandPool"]["task_id"]
    status = await wait_for_task_result(task_id, 60)
    assert (status is not None) and (status == TaskStatus.FINISHED.name)

    # prepare VMs in pool
    qu = (
        """
    mutation {
        preparePool(pool_id: "%s"){
            ok
            task_id
        }
    }"""
        % pool_id
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["preparePool"]["ok"]

    task_id = executed["preparePool"]["task_id"]
    status = await wait_for_task_result(task_id, 60)
    assert (status is not None) and (status == TaskStatus.FINISHED.name)


@pytest.mark.asyncio
async def test_update_automated_pool(
    snapshot,
    fixt_redis_client,
    fixt_db,
    fixt_create_automated_pool,  # noqa
    fixt_auth_context,
):  # noqa
    """Create automated pool, update this pool, remove this pool"""

    # check that pool was successfully created'
    assert fixt_create_automated_pool["is_pool_successfully_created"]

    pool_id = fixt_create_automated_pool["id"]

    # update some params
    new_pool_name = "test-pool-{}".format(str(uuid.uuid4())[:7])
    qu = """
    mutation {
        updateDynamicPool(
            pool_id: "%s"
            verbose_name: "%s",
            reserve_size: 1,
            total_size: 4,
            increase_step: 2,
            keep_vms_on: true,
            vm_action_upon_user_disconnect: SHUTDOWN,
            vm_disconnect_action_timeout: 55,
            vm_name_template: "vdi-test",
            ad_ou: "",
            create_thin_clones: true,
            enable_vms_remote_access: true,
            start_vms: true,
            set_vms_hostnames: false,
            include_vms_in_ad: false){
            ok
        }
    }""" % (
        pool_id,
        new_pool_name,
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["updateDynamicPool"]["ok"]

    # Check
    qu = """
    {
        pool(pool_id: "%s") {
            status
            reserve_size
            total_size
            increase_step
            keep_vms_on
            pool_type
            vm_disconnect_action_timeout
            vm_action_upon_user_disconnect
        }
    }
    """ % pool_id
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    snapshot.assert_match(executed)

    # decrease total_size (Это особый случай и запустит задачу в воркере)
    qu = (
        """
    mutation {
        updateDynamicPool(
            pool_id: "%s"
            total_size: 3){
            ok
        }
    }"""
        % pool_id
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["updateDynamicPool"]["ok"]


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    "fixt_redis_client",
    "fixt_db",
    "fixt_user_admin",  # noqa
    "fixt_create_automated_pool",
    "fixt_user_another_admin",
)  # noqa
class PoolTestCase(VdiHttpTestCase):
    @gen_test(timeout=VEIL_WS_MAX_TIME_TO_WAIT + 10)
    def test_automated_pool_expand(self):
        # Инициализация лицензии происходит в VdiHttpTestCase
        pool = yield Pool.query.gino.first()
        pool_type = pool.pool_type
        self.assertEqual(pool_type, Pool.PoolTypes.AUTOMATED)
        pool_id = pool.id

        vms_amount = yield pool.get_vm_amount()
        self.assertEqual(vms_amount, 1)  # Сначала в пуле должна быть 1 VM

        # Авторизуемся, чтобы получить токен
        body = '{"username": "test_user_admin","password": "veil"}'
        response_dict = yield self.get_response(body=body, url="/auth")
        access_token = response_dict["data"]["access_token"]
        self.assertTrue(access_token)

        # Формируем данные для тестируемого параметра
        headers = {
            "Content-Type": "application/json",
            "Authorization": "jwt {}".format(access_token),
        }
        body = '{"remote_protocol": "spice"}'
        url = "/client/pools/{pool_id}/".format(pool_id=pool_id)

        response_dict = yield self.get_response(body=body, url=url, headers=headers)

        if "errors" in response_dict:
            # Исключение на случай отсутствия лицензии
            response_data = response_dict["errors"][0]
            response_code = response_data["code"]
            self.assertIn(response_code, ["001", "002", "404"])
        else:
            response_data = response_dict["data"]
            self.assertIsInstance(response_data, dict)
            self.assertIn("port", response_data)

            # Расширение пула не могло произойти так быстро, поэтому убеждаемся, что нет свободных ВМ.
            # Авторизуемся под вторым админом, чтобы получить токен
            body = '{"username": "test_user_admin2","password": "veil"}'
            response_dict = yield self.get_response(body=body, url="/auth")
            access_token = response_dict["data"]["access_token"]
            self.assertTrue(access_token)

            # Формируем данные для тестируемого параметра
            headers = {
                "Content-Type": "application/json",
                "Authorization": "jwt {}".format(access_token),
            }
            body = '{"remote_protocol": "spice"}'
            url = "/client/pools/{pool_id}/".format(pool_id=pool_id)

            response_dict = yield self.get_response(body=body, url=url, headers=headers)
            self.assertIsInstance(response_dict, dict)
            port = response_data["port"]
            self.assertEqual(5900, port)

            # Ждем время ожидания монитора ресурсов + накладки, чтобы убедиться, что пул расширился
            yield gen.sleep(5)

            vms_amount = yield pool.get_vm_amount()
            self.assertEqual(2, vms_amount)  # Тут ожидаем, что уже 2


@pytest.mark.asyncio
async def test_copy_automated_pool(
    fixt_redis_client,
    fixt_db,
    fixt_create_automated_pool,  # noqa
    fixt_auth_context,
):  # noqa
    """Create automated pool, update this pool, remove this pool"""

    # check that pool was successfully created'
    assert fixt_create_automated_pool["is_pool_successfully_created"]

    pool_id = fixt_create_automated_pool["id"]

    qu = """
    mutation {
        copyDynamicPool(
            pool_id: "%s"){
            pool_settings
        }
    }""" % (
        pool_id,
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["copyDynamicPool"]["pool_settings"]

# ----------------------------------------------


# Static pool
@pytest.mark.asyncio
async def test_create_static_pool(
    fixt_redis_client, fixt_db, fixt_create_static_pool, fixt_auth_context  # noqa
):  # noqa
    """Create static pool, make request to check data, remove this pool"""
    pool_id = fixt_create_static_pool["id"]
    assert fixt_create_static_pool["ok"]

    # Ждем окончания подготовки вм, что была включена в пул
    vm_ids = await Vm.get_vms_ids_in_pool(pool_id)
    assert len(vm_ids) == 1
    tasks = await Task.get_tasks_associated_with_entity(vm_ids[0])
    status = await wait_for_task_result(tasks[0].id, 20)
    is_vm_successfully_prepared = (status is not None) and (
        status == TaskStatus.FINISHED.name
    )
    assert is_vm_successfully_prepared

    # get pool info
    ordering_list = [
        "verbose_name",
        "user",
        "status",
        "qemu_state",
        "parent_name",
    ]
    for ordering in ordering_list:
        qu = (
            """{
          pool(pool_id: "%s") {
            pool_type
              vms (ordering: "%s"){
                verbose_name
            }
          }
        }"""
            % (pool_id, ordering)
        )
        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
        assert len(executed["pool"]["vms"]) == 1


@pytest.mark.asyncio
async def test_update_static_pool(
    snapshot, fixt_redis_client, fixt_db, fixt_create_static_pool, fixt_auth_context  # noqa
):  # noqa
    """Create static pool, update this pool, remove this pool"""
    pool_id = fixt_create_static_pool["id"]

    new_pool_name = "test-pool-{}".format(str(uuid.uuid4())[:7])
    qu = """
    mutation {
        updateStaticPool(
            pool_id: "%s",
            verbose_name: "%s",
            keep_vms_on: true,
            vm_disconnect_action_timeout: 55){
         ok
    }
    }""" % (
        pool_id,
        new_pool_name,
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["updateStaticPool"]["ok"]

    # Check
    qu = """
    {
        pool(pool_id: "%s") {
            status
            keep_vms_on
            pool_type
            vm_disconnect_action_timeout
            vm_action_upon_user_disconnect
        }
    }
    """ % pool_id
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    snapshot.assert_match(executed)


@pytest.mark.asyncio
async def test_remove_and_add_vm_in_static_pool(
    fixt_redis_client,
    fixt_db,
    fixt_controller,  # noqa
    fixt_create_static_pool,
    fixt_auth_context,
):  # noqa
    """Create automated pool, make request to check data,
    remove a vm from this pool, add the removed vm back to this pool, remove this pool"""
    pool_id = fixt_create_static_pool["id"]

    # get pool info
    qu = (
        """{
      pool(pool_id: "%s") {
        pool_type
        users_count
        users(ordering: "id") {
                    id
        }
        vms {
          id
          verbose_name
        }
      }
    }"""
        % pool_id
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)

    vms_in_pool_list = executed["pool"]["vms"]
    assert len(vms_in_pool_list) == 1

    # remove first vm from pool
    vm_id = vms_in_pool_list[0]["id"]
    vm_verbose_name = vms_in_pool_list[0]["verbose_name"]
    qu = """
      mutation {
        removeVmsFromStaticPool(pool_id: "%s", vm_ids: ["%s"]){
          ok
          task_id
        }
      }""" % (
        pool_id,
        vm_id,
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)

    # Проверить успешно ли стартовала задача
    assert executed["removeVmsFromStaticPool"]["ok"]

    # Дожидаемся завершения задачи
    task_id = executed["removeVmsFromStaticPool"]["task_id"]
    status = await wait_for_task_result(task_id, 15)
    assert (status is not None) and (status == TaskStatus.FINISHED.name)

    # add removed machine back to pool
    qu = """
      mutation {
                addVmsToStaticPool(pool_id: "%s", vms: [{id: "%s", verbose_name: "%s"}]){
                    ok
                  }
                }""" % (
        pool_id,
        vm_id,
        vm_verbose_name,
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["addVmsToStaticPool"]["ok"]


@pytest.mark.asyncio
async def test_clear_pool_errors(
    fixt_redis_client,
    fixt_db,
    fixt_controller,  # noqa
    fixt_create_static_pool,
    fixt_auth_context,
):  # noqa
    """Create automated pool, make request to check data,
    remove a vm from this pool, add the removed vm back to this pool, remove this pool"""
    pool_id = fixt_create_static_pool["id"]
    pool = await Pool.get(pool_id)
    await pool.update(status=Status.FAILED).apply()
    query = (
        """mutation{
                    clearPool(pool_id: "%s")
                        {
                          ok
                        }
                    }"""
        % pool_id
    )
    executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
    assert executed["clearPool"]["ok"]

    await pool.update(status=Status.SERVICE).apply()
    query = (
        """mutation{
                    clearPool(pool_id: "%s")
                        {
                          ok
                        }
                    }"""
        % pool_id
    )
    try:
        await execute_scheme(pool_schema, query, context=fixt_auth_context)
    except ExecError as E:
        assert "находится в сервисном режиме." in str(E)
    else:
        raise AssertionError

    await pool.update(status=Status.ACTIVE).apply()
    query = (
        """mutation{
                    clearPool(pool_id: "%s")
                        {
                          ok
                        }
                    }"""
        % pool_id
    )
    try:
        await execute_scheme(pool_schema, query, context=fixt_auth_context)
    except ExecError as E:
        assert "уже активирован." in str(E)
    else:
        raise AssertionError


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    "fixt_redis_client",
    "fixt_db",
    "fixt_controller",
    "fixt_group",
    "fixt_user",
    "fixt_create_static_pool",
)
class TestPoolPermissionsSchema:
    async def test_pool_user_permission(self, snapshot, fixt_auth_context):  # noqa
        pools = await Pool.query.gino.all()
        pool = pools[0]
        query = (
            """mutation{
                            entitleUsersToPool(pool_id: "%s",
                                               users: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                            {
                                ok,
                                pool{users{id}}
                            }}"""
            % pool.id
        )

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

        query = (
            """mutation{
                    removeUserEntitlementsFromPool(pool_id: "%s",
                                       users: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                    {
                        ok,
                        pool{users{id}}
                    }}"""
            % pool.id
        )

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_pool_group_permission(self, snapshot, fixt_auth_context):  # noqa
        pools = await Pool.query.gino.all()
        pool = pools[0]
        query = (
            """mutation{
                                    addPoolGroup(pool_id: "%s",
                                                 groups: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                                    {
                                        ok,
                                        pool{assigned_groups{id}, possible_groups{id}}
                                    }}"""
            % pool.id
        )

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

        query = (
            """mutation{
                            removePoolGroup(pool_id: "%s",
                                            groups: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"])
                            {
                                ok,
                                pool{assigned_groups{id}, possible_groups{id}}
                            }}"""
            % pool.id
        )

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)


@pytest.mark.asyncio
async def test_pools_ordering(
    fixt_redis_client,
    fixt_db,
    fixt_controller,
    fixt_create_automated_pool,  # noqa
    fixt_auth_context,
):  # noqa

    ordering_list = [
        "verbose_name",
        "controller_address",
        "users_count",
        "vm_amount",
        "pool_type",
    ]
    for ordering in ordering_list:
        qu = (
            """
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
                    resource_pool_id
                    resource_pool {
                      verbose_name
                    }
                    datapool {
                      verbose_name
                    }
                    template_id
                    template {
                      verbose_name
                    }
                    initial_size
                    os_type
                    assigned_groups(ordering: "verbose_name") {
                      id
                      verbose_name
                    }
                    possible_groups {
                      id
                      verbose_name
                    }
                    users_count(entitled: false)
                    users(entitled: false) {
                      id
                    }
                    assigned_connection_types
                    possible_connection_types
                    vm_amount
                    vms {
                      verbose_name
                      assigned_users(username: "n") {
                        id
                      }
                      assigned_users_count
                      possible_users(username: "n"){
                        username
                        is_superuser
                        date_joined
                      }
                      possible_users_count
                      count
                      events {
                        message
                      }
                      backups {
                        filename
                      }
                      # spice_connection {
                      #   connection_url
                      # }
                      # vnc_connection {
                      #   connection_url
                      # }
                    }
                 }
                }
            """
            % ordering
        )

        await execute_scheme(pool_schema, qu, context=fixt_auth_context)


@pytest.mark.asyncio
async def test_create_update_remove_rds_pool(fixt_db, fixt_create_rds_pool, fixt_auth_context):  # noqa
    """Create update remove RDS pool"""

    assert fixt_create_rds_pool["ok"]
    pool_id = fixt_create_rds_pool["id"]

    # Update
    new_pool_name = "test-pool-{}".format(str(uuid.uuid4())[:7])
    qu = """
    mutation {
        updateRdsPool(pool_id: "%s", verbose_name: "%s", keep_vms_on: true){
         ok
    }
    }""" % (
        pool_id,
        new_pool_name,
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["updateRdsPool"]["ok"]


@pytest.mark.asyncio
async def test_add_remove_vm_to_rds_pool(
    fixt_redis_client,
    fixt_db,
    fixt_create_rds_pool,
    fixt_auth_context
):  # noqa
    """Create update remove RDS pool"""

    assert fixt_create_rds_pool["ok"]
    pool_id = fixt_create_rds_pool["id"]

    # Add VM
    added_vm_id = uuid.uuid4()
    added_vm_verbose_name = "added_rds_vm"
    qu = """
      mutation {
                addVmsToRdsPool(pool_id: "%s", vms: [{id: "%s", verbose_name: "%s"}]){
                    ok
                  }
                }""" % (
        pool_id,
        added_vm_id,
        added_vm_verbose_name,
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["addVmsToRdsPool"]["ok"]

    # Remove VM
    qu = """
      mutation {
        removeVmsFromRdsPool(pool_id: "%s", vm_ids: ["%s"]){
          ok
          task_id
        }
      }""" % (
        pool_id,
        added_vm_id,
    )
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)

    # Проверить успешно ли стартовала задача
    assert executed["removeVmsFromRdsPool"]["ok"]

    # Дожидаемся завершения задачи
    task_id = executed["removeVmsFromRdsPool"]["task_id"]
    status = await wait_for_task_result(task_id, 15)
    assert (status is not None) and (status == TaskStatus.FINISHED.name)


@pytest.mark.asyncio
async def test_vm_connection_data(
    snapshot, fixt_redis_client, fixt_db, fixt_create_static_pool, fixt_auth_context):  # noqa
    """Add vm_connection_data, update this vm_connection_data, remove this vm_connection_data"""

    pool_id = fixt_create_static_pool["id"]
    pool = await Pool.get(pool_id)
    vms = await pool.get_vms()
    vm_id = vms[0].id

    address = "192.168.6.6"
    port = 6669
    connection_type = "SPICE"
    active = "true"

    # Add
    qu = """
    mutation {
      addVmConnectionData(vm_id:"%s", address:"%s", port:%s, connection_type:%s, active:%s){
        ok
        vm_connection_data {
          id
          address
          port
          connection_type
          active
        }
      }  
    }""" % (vm_id, address, port, connection_type, active)

    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    vm_connection_data_id = executed["addVmConnectionData"]["vm_connection_data"]["id"]

    assert vm_connection_data_id
    assert executed["addVmConnectionData"]["ok"]
    assert executed["addVmConnectionData"]["vm_connection_data"]["address"] == address
    assert executed["addVmConnectionData"]["vm_connection_data"]["port"] == port
    assert executed["addVmConnectionData"]["vm_connection_data"]["connection_type"] == "PoolConnectionTypes.SPICE"
    assert executed["addVmConnectionData"]["vm_connection_data"]["active"]

    # Update
    new_address = "192.168.3.9"
    new_port = 5642
    new_active = "false"
    qu = """
    mutation {
      updateVmConnectionData(id:"%s", vm_id:"%s", connection_type:%s, address:"%s", port:%s, active:%s){
        ok
      }
    }""" % (vm_connection_data_id, vm_id, connection_type, new_address, new_port, new_active)

    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["updateVmConnectionData"]["ok"]

    # Request data
    qu = """{
      pool(pool_id:"%s") {
        vms{
          id
          vm_connection_data_list{
            id
            address
            port
            connection_type
            active
          }
          vm_connection_data_count
        }
      }
    }""" % pool_id
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["pool"]["vms"][0]["vm_connection_data_count"] == 1
    assert executed["pool"]["vms"][0]["vm_connection_data_list"][0]["address"] == new_address
    assert executed["pool"]["vms"][0]["vm_connection_data_list"][0]["port"] == new_port
    assert not executed["pool"]["vms"][0]["vm_connection_data_list"][0]["active"]

    # Delete
    qu = """
    mutation {
      removeVmConnectionData(id:"%s"){
        ok
      }
    }""" % vm_connection_data_id
    executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
    assert executed["removeVmConnectionData"]["ok"]
