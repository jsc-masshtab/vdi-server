# -*- coding: utf-8 -*-
import pytest

from web_app.controller.schema import controller_schema
from common.models.controller import Controller
from web_app.tests.utils import execute_scheme
from web_app.tests.fixtures import fixt_db, fixt_controller, fixt_auth_context, fixt_veil_client  # noqa
from common.settings import PAM_AUTH

pytestmark = [pytest.mark.controllers, pytest.mark.skipif(PAM_AUTH, reason="not finished yet")]


@pytest.mark.asyncio
async def test_add_update_remove_controller(fixt_db, fixt_auth_context, fixt_controller):  # noqa
    """Add, update and remove controller"""

    controller_id = fixt_controller['controller_id']

    # update controller
    qu = """
    mutation {
        updateController(
            id_: "%s",
            verbose_name: "NEW_NAME",
            description: "controller for development and testing") {
            controller {
                id
                verbose_name
                description
                address
                status
            }
    }
    }
    """ % controller_id

    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)
    assert executed['updateController']['controller']


@pytest.mark.asyncio
async def test_credentials(fixt_db, snapshot, fixt_controller, fixt_auth_context):  # noqa

    controller_id = await Controller.select('id').gino.scalar()
    qu = """
        mutation {
            testController(id_: "%s") {
                ok
            }
        }
        """ % controller_id
    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)


@pytest.mark.asyncio
async def test_resolve_controllers(fixt_db, snapshot, fixt_controller, fixt_auth_context):  # noqa
    qu = """
            {
              controllers {
                verbose_name
                description
                address
                version
              }
            }
        """
    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)


@pytest.mark.asyncio
async def test_resolve_controller(fixt_db, snapshot, fixt_controller, fixt_auth_context):  # noqa

    controller_id = await Controller.select('id').gino.scalar()
    qu = """
            {
              controller(id_: "%s") {
                verbose_name
                address
                description
                status
                version
                token
                # Новые поля
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
             }
            }""" % controller_id
    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)
