# -*- coding: utf-8 -*-
import pytest

from web_app.controller.schema import controller_schema
from common.models.controller import Controller
from web_app.tests.utils import execute_scheme
from web_app.tests.fixtures import (
    fixt_db,
    fixt_redis_client,
    fixt_controller,
    fixt_auth_context,
    fixt_veil_client,
)  # noqa
from common.settings import PAM_AUTH
from common.veil.veil_gino import Status

pytestmark = [
    pytest.mark.controllers,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


@pytest.mark.asyncio
async def test_add_update_remove_controller(
    fixt_db, fixt_auth_context, fixt_controller
):  # noqa
    """Add, update and remove controller"""

    controller_id = fixt_controller["controller_id"]

    # update controller
    qu = (
        """
    mutation {
        updateController(
            id_: "%s",
            verbose_name: "NEW_NAME",
            description: "controller for development and testing",
            token: "jwt eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxOTEyOTM3NjExLCJzc28iOmZhbHNlLCJvcmlnX2lhdCI6MTU5ODQ0MTYxMX0.OSRio0EoWA8ZDtvzl3YlaBmdfbI0DQz1RiGAIMCgoX0") {
            controller {
                id
                verbose_name
                description
                address
                status
            }
    }
    }
    """
        % controller_id
    )

    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)
    assert executed["updateController"]["controller"]


@pytest.mark.asyncio
async def test_credentials(
    fixt_db, snapshot, fixt_controller, fixt_auth_context
):  # noqa

    controller_id = await Controller.select("id").gino.scalar()
    qu = (
        """
        mutation {
            testController(id_: "%s") {
                ok
            }
        }
        """
        % controller_id
    )
    executed = await execute_scheme(
        controller_schema, qu, context=fixt_auth_context
    )  # noqa
    snapshot.assert_match(executed)


@pytest.mark.asyncio
@pytest.mark.smoke_test
async def test_resolve_controllers(
    fixt_db, snapshot, fixt_controller, fixt_auth_context
):  # noqa
    qu = """
            {
              controllers(status: ACTIVE) {
                verbose_name
                description
                address
                version
              }
            }
        """
    executed = await execute_scheme(
        controller_schema, qu, context=fixt_auth_context
    )  # noqa
    snapshot.assert_match(executed)


@pytest.mark.asyncio
async def test_resolve_controller(
    fixt_db, snapshot, fixt_controller, fixt_auth_context
):  # noqa

    controller_id = await Controller.select("id").gino.scalar()
    qu = (
        """
            {
              controller(id_: "%s") {
                verbose_name
                address
                description
                status
                version
                token
                pools {
                  verbose_name
                  status
                  vms_amount
                  users_amount
                  pool_type
                  keep_vms_on
                }
                # Ресуры на VeiL
                clusters {
                  id
                  verbose_name
                  nodes_count
                  status
                  cpu_count
                  memory_count
                  tags
                }
                nodes {
                  id
                  verbose_name
                  status
                  cpu_count
                  memory_count
                  management_ip
                }
                resource_pools {
                  id
                  verbose_name
                }
                data_pools {
                  id
                  verbose_name
                  used_space
                  free_space
                  size
                  status
                  type
                  vdisk_count
                  tags
                  hints
                  file_count
                  iso_count
                }
                vms {
                  id
                  verbose_name
                }
                templates {
                  id
                  verbose_name
                }
                veil_events_count
                veil_events {
                  id
                }
             }
            }"""
        % controller_id
    )
    executed = await execute_scheme(
        controller_schema, qu, context=fixt_auth_context
    )  # noqa
    snapshot.assert_match(executed)


@pytest.mark.asyncio
async def test_service_controller_mode(
    fixt_db, fixt_controller, fixt_auth_context
):  # noqa
    controller = await Controller.get(fixt_controller["controller_id"])
    qu = (
        """
        mutation {
            serviceController(id_: "%s") {
                ok
            }
        }
        """
        % controller.id
    )
    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)
    assert executed["serviceController"]["ok"]

    qu = (
        """
        mutation {
            activateController(id_: "%s") {
                ok
            }
        }
        """
        % controller.id
    )
    await execute_scheme(controller_schema, qu, context=fixt_auth_context)
    assert controller.status == Status.ACTIVE
