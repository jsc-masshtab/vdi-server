import pytest

from graphene.test import Client  # noqa

from web_app.tests.utils import execute_scheme
from web_app.tests.fixtures import fixt_db, fixt_controller, fixt_user_admin, fixt_create_automated_pool, fixt_auth_context  # noqa

from web_app.controller.resource_schema import resources_schema


pytestmark = [pytest.mark.asyncio, pytest.mark.resources]


async def test_request_clusters(fixt_db, snapshot, fixt_controller, fixt_auth_context):  # noqa

    """Request clusters data"""
    examples = ["verbose_name", "-cpu_count"]
    for ordering in examples:
        qu = """{
                  clusters(ordering: "%s"){
                    verbose_name
                    id
                    nodes_count
                    controller{
                        id
                        }
                    }
                }""" % ordering

        executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)

    cluster = executed['clusters'][0]

    qu = """{
                cluster(cluster_id: "%s", controller_id: "%s"){
                    verbose_name
                }
            }""" % (cluster['id'], cluster['controller']['id'])

    executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)


async def test_request_nodes(fixt_db, fixt_controller, snapshot, fixt_auth_context):  # noqa

    """Request nodes data"""
    examples = ["verbose_name", "-cpu_count"]
    for ordering in examples:
        qu = """{
                  nodes(ordering: "%s"){
                    id
                    cpu_count
                    verbose_name
                    controller{
                        id
                        }
                    }
                }""" % ordering

        executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)
        snapshot.assert_match(executed)

    node = executed['nodes'][0]

    qu = """{
              node(node_id: "%s", controller_id: "%s"){
                verbose_name
                status
                cpu_count
                memory_count
                management_ip
              }
            }""" % (node['id'], node['controller']['id'])

    executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)


async def test_request_datapools(fixt_db, fixt_controller, snapshot, fixt_auth_context):  # noqa

    """Request datapools data"""
    examples = ["verbose_name", "-type"]
    for ordering in examples:
        qu = """{
                  datapools(ordering: "%s"){
                    id
                    verbose_name
                    controller{
                        id
                        }
                  }
                }""" % ordering

        executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)

    datapool = executed['datapools'][0]

    qu = """{
              datapool(datapool_id: "%s", controller_id: "%s"){
                verbose_name
                size
                status
                type
                free_space
              }
            }""" % (datapool['id'], datapool['controller']['id'])

    executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)


async def test_request_vms(fixt_db, fixt_controller, snapshot, fixt_auth_context):  # noqa

    """Request vms data"""
    examples = ["verbose_name", "-status"]
    for ordering in examples:
        qu = """{
                  vms(ordering: "%s", limit: 5, offset: 0){
                    verbose_name
                    id
                    status
                    memory_count
                    cpu_count
                    controller{
                        id
                        }
                  }
                }""" % ordering

        executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)

    vm = executed['vms'][0]

    qu = """{
              vm(vm_id: "%s", controller_id: "%s"){
                verbose_name
                id
                status
                memory_count
                cpu_count
              }
            }""" % (vm['id'], vm['controller']['id'])

    executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)


async def test_request_templates(fixt_db, fixt_controller, snapshot, fixt_auth_context):  # noqa

    """Request templates data"""
    examples = ["verbose_name", "-status"]
    for ordering in examples:
        qu = """{
                  templates(ordering: "%s", limit: 5, offset: 0){
                    id
                    verbose_name
                    controller {
                      id
                      verbose_name
                    }
                    status
                  }
                }""" % ordering

        executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)

    template = executed['templates'][0]

    qu = """{
              template(template_id: "%s", controller_id: "%s"){
                verbose_name
                status
              }
            }""" % (template['id'], template['controller']['id'])

    executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
    snapshot.assert_match(executed)
