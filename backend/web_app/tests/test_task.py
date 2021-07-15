# -*- coding: utf-8 -*-
import pytest
import asyncio

from web_app.task.schema import task_schema
from web_app.tests.utils import execute_scheme
from web_app.tests.fixtures import (
    fixt_db,
    fixt_redis_client,
    fixt_controller,
    fixt_create_automated_pool,
    fixt_create_static_pool,  # noqa
    fixt_auth_context,
    fixt_group,
    fixt_user,
    fixt_user_admin,
    fixt_user_another_admin,  # noqa
    fixt_launch_workers,
    fixt_veil_client,
    get_resources_for_pool_test,
    get_auth_context,
)  # noqa
from web_app.pool.schema import pool_schema
from common.models.task import Task
from common.settings import PAM_AUTH


pytestmark = [
    pytest.mark.tasks,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


@pytest.mark.asyncio
async def test_request_tasks(fixt_db, fixt_auth_context):  # noqa

    """Request tasks info"""
    qu = """{
            tasks(status:IN_PROGRESS, ordering: "status"){
                id
                task_type
                status
                entity_id
                priority
                created
             }
        }"""
    await execute_scheme(task_schema, qu, context=fixt_auth_context)


# @pytest.mark.broken_runner
@pytest.mark.asyncio
async def test_cancel_tasks(
    fixt_launch_workers, fixt_db, fixt_controller, fixt_auth_context
):  # noqa

    # Start pool creation task
    await asyncio.sleep(1)  # дать время процу воркеру запуститься
    resources = await get_resources_for_pool_test()
    qu = """
            mutation {
                      addDynamicPool(
                        connection_types: [SPICE, RDP],
                        verbose_name: "pool-name",
                        controller_id: "%s",
                        resource_pool_id: "%s",
                        template_id: "%s",
                        vm_name_template: "vdi-test") {
                          pool {
                            pool_id
                          },
                          ok
                        }
                    }""" % (
        resources["controller_id"],
        resources["resource_pool_id"],
        resources["template_id"],
    )
    context = await get_auth_context()
    executed = await execute_scheme(pool_schema, qu, context=context)

    assert executed["addDynamicPool"]["ok"]

    pool_id = executed["addDynamicPool"]["pool"]["pool_id"]
    tasks = await Task.get_tasks_associated_with_entity(pool_id)
    task_id = tasks[0].id

    # wait for task start
    await asyncio.sleep(1)

    # stop task
    qu = (
        """mutation{
              cancelTask(task: "%s"){
                  ok
              }
      }"""
        % task_id
    )
    executed = await execute_scheme(task_schema, qu, context=fixt_auth_context)
    assert executed["cancelTask"]["ok"]

    # delete pool
    qu = (
        """
    mutation {
      removePool(pool_id: "%s", full: true) {
        ok
      }
    }
    """
        % pool_id
    )
    executed = await execute_scheme(pool_schema, qu, context=context)
    assert executed["removePool"]["ok"]
