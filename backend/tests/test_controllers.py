# -*- coding: utf-8 -*-
import pytest

from controller.schema import controller_schema
from controller.models import Controller
from tests.utils import execute_scheme
from tests.fixtures import fixt_db, fixt_controller, fixt_auth_context  # noqa


pytestmark = [pytest.mark.asyncio, pytest.mark.controllers]


async def test_add_update_remove_controller(fixt_db, fixt_auth_context):  # noqa
    """Add, update and remove controller"""
    controller_ip = '192.168.11.102'

    # add controller
    qu = """
    mutation {
        addController(
            verbose_name: "controller_added_during_test",
            address: "%s",
            description: "controller_added_during_test",
            username: "test_vdi_user",
            password: "test_vdi_user",
            ldap_connection: false) {
                ok
                controller
                {
                    id
                    verbose_name
                    description
                    address
                    status
                }
            }
    }
    """ % controller_ip

    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)
    assert executed['addController']['ok']

    controller_id = executed['addController']['controller']['id']

    # update controller
    qu = """
    mutation {
        updateController(
            id: "%s",
            verbose_name: "NEW_NAME",
            address: "%s",
            description: "controller for development and testing",
            username: "test_vdi_user",
            password: "test_vdi_user",
            ldap_connection: false) {
            ok
            controller {
                id
                verbose_name
                description
                address
                status
            }
  }
}
    """ % (controller_id, controller_ip)

    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)
    assert executed['updateController']['ok']

    # remove controller
    qu = """
    mutation {
        removeController(id: "%s") {
            ok
        }
    }
    """ % controller_id

    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)
    assert executed['removeController']['ok']


@pytest.mark.asyncio
async def test_credentials(fixt_db, snapshot, fixt_controller, fixt_auth_context):  # noqa

    controller_id = await Controller.select('id').gino.scalar()
    qu = """
        mutation {
                testController(id: "%s") {
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
                id
                verbose_name
                description
                address
                version
              }
            }
        """
    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)
