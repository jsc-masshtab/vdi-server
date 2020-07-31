# -*- coding: utf-8 -*-
import pytest

from web_app.controller.schema import controller_schema
# from common.models.controller import Controller
from web_app.tests.utils import execute_scheme
from web_app.tests.fixtures import fixt_db, fixt_controller, fixt_auth_context  # noqa


pytestmark = [pytest.mark.controllers]


@pytest.mark.asyncio
async def test_add_update_remove_controller(fixt_db, fixt_auth_context):  # noqa
    """Add, update and remove controller"""
    pass
    controller_ip = '192.168.11.115'

    # add controller
    qu = """
    mutation {
        addController(
            verbose_name: "controller_added_during_test",
            address: "%s",
            description: "controller_added_during_test",
            token: "jwt eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxNjUsInVzZXJuYW1lIjoiYXBpLWNsaSIsImV4cCI6MTkwODI2MjI1Niwic3NvIjpmYWxzZSwib3JpZ19pYXQiOjE1OTM3NjYyNTZ9._41CVXezP1vDHoZyQ71UcadqPdti7-tmy_teEjfBgio") {
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
    assert executed['addController']['controller']

    controller_id = executed['addController']['controller']['id']

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

    # remove controller
    qu = """
    mutation {
        removeController(id_: "%s") {
            ok
        }
    }
    """ % controller_id

    executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)
    assert executed['removeController']['ok']


# @pytest.mark.asyncio
# async def test_credentials(fixt_db, snapshot, fixt_controller, fixt_auth_context):  # noqa
#
#     controller_id = await Controller.select('id').gino.scalar()
#     qu = """
#         mutation {
#                 testController(id_: "%s") {
#                     ok
#                 }
#         }
#         """ % controller_id
#     executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)  # noqa
#     snapshot.assert_match(executed)


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


# @pytest.mark.asyncio
# async def test_resolve_controller(fixt_db, snapshot, fixt_controller, fixt_auth_context):  # noqa
#
#     controller_id = await Controller.select('id').gino.scalar()
#     qu = """
#             {
#               controller(id_: "%s") {
#                 id
#                 verbose_name
#                 address
#                 description
#                 status
#                 version
#                 token
#                 # Новые поля
#                 pools {
#                   verbose_name
#                   status
#                   vms_amount
#                   users_amount
#                   pool_type
#                   keep_vms_on
#                 }
#                 # Ресуры на VeiL
#                 clusters {
#                   id
#                   verbose_name
#                   nodes_count
#                   status
#                   cpu_count
#                   memory_count
#                   tags
#                 }
#                 nodes {
#                   id
#                   verbose_name
#                   status
#                   cpu_count
#                   memory_count
#                   management_ip
#                 }
#                 data_pools {
#                   id
#                   verbose_name
#                   used_space
#                   free_space
#                   size
#                   status
#                   type
#                   vdisk_count
#                   tags
#                   hints
#                   file_count
#                   iso_count
#                 }
#                 vms {
#                   id
#                   verbose_name
#                   template
#                 }
#                 templates {
#                   id
#                   verbose_name
#                   template
#                 }
#
#              }
#             }""" % controller_id
#     executed = await execute_scheme(controller_schema, qu, context=fixt_auth_context)  # noqa
#     snapshot.assert_match(executed)
