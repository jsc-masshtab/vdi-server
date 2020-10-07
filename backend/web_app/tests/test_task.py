# -*- coding: utf-8 -*-
import pytest

from web_app.task.schema import task_schema
from web_app.tests.utils import execute_scheme
from web_app.tests.fixtures import (fixt_db, fixt_controller, fixt_create_automated_pool, fixt_create_static_pool,  # noqa
                            fixt_auth_context, fixt_group, fixt_user, fixt_user_admin, fixt_user_another_admin, # noqa
                            fixt_launch_workers)  # noqa


pytestmark = [pytest.mark.tasks]


@pytest.mark.asyncio
async def test_request_tasks(fixt_db, fixt_controller, fixt_auth_context):

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


@pytest.mark.asyncio
async def test_cancel_tasks(fixt_db, fixt_controller, fixt_auth_context):

    qu = """mutation{
                cancelTask(cancel_all: true){
                    ok
                }
        }"""
    executed = await execute_scheme(task_schema, qu, context=fixt_auth_context)
    assert executed['cancelTask']['ok']
