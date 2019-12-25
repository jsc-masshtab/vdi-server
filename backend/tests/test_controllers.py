import pytest
import asyncio

from controller.schema import controller_schema

from tests.utils import execute_scheme
from tests.fixtures import fixt_db, auth_context_fixture


@pytest.mark.asyncio
@pytest.mark.controllers
async def test_add_remove_controller(fixt_db, auth_context_fixture):

    controller_ip = '192.168.6.122'

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

    executed = await execute_scheme(controller_schema, qu, context=auth_context_fixture)
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
    executed = await execute_scheme(controller_schema, qu, context=auth_context_fixture)
    assert executed['updateController']['ok']

    # remove controller
    qu = """
    mutation {
        removeController(id: "%s") {
            ok
        }
    }
    """ % controller_id

    executed = await execute_scheme(controller_schema, qu, context=auth_context_fixture)
    assert executed['removeController']['ok']

