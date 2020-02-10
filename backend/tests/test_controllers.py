# -*- coding: utf-8 -*-
import pytest

from controller.schema import controller_schema
from tests.utils import execute_scheme
from tests.fixtures import fixt_db, auth_context_fixture  # noqa


pytestmark = [pytest.mark.controllers]


@pytest.mark.asyncio
async def test_add_update_remove_controller(fixt_db, auth_context_fixture):  # noqa
    """Add, update and remove controller"""
    controller_ip = '192.168.20.120'  # TODO: заменить на контроллер из вагранта

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
    print('\n222222')
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
    print('\n33333333')
    executed = await execute_scheme(controller_schema, qu, context=auth_context_fixture)
    assert executed['removeController']['ok']
