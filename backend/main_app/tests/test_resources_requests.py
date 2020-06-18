import pytest

from graphene.test import Client  # noqa

from tests.utils import execute_scheme
from tests.fixtures import fixt_db, fixt_controller, fixt_user_admin, fixt_create_automated_pool, fixt_auth_context  # noqa

from controller_resources.schema import resources_schema
from pool.models import Pool
from controller.models import Controller


pytestmark = [pytest.mark.resources]


@pytest.mark.asyncio
async def test_request_clusters(fixt_db, fixt_auth_context):  # noqa
    """Request clusters data"""
    list = ["verbose_name", "cpu_count", "memory_count", "nodes_count", "status", "controller"]
    for ordering in list:
        qu = """
        {
            clusters (ordering: "%s"){
                verbose_name
                id
                nodes_count
                datapools{
                    verbose_name
                }
                nodes{
                    verbose_name
                }
            }
        }
        """ % ordering

        executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa


@pytest.mark.asyncio
async def test_request_nodes(fixt_db, fixt_auth_context):  # noqa
    """Request nodes data"""
    list = ["verbose_name", "cpu_count", "memory_count", "datacenter_name", "status", "controller", "management_ip"]
    for ordering in list:
        qu = """
        {
            nodes (ordering: "%s"){
            id
            cpu_count
            verbose_name
            cluster{
                verbose_name
            }
            controller {
                address
            }
        }
        }
        """ % ordering
        executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)

        # Чекним запрос определенного сервера (первого в списке), если серверы есть
        if executed['nodes']:
            # print('__executed', executed)
            node = executed['nodes'][0]

            qu = """
            {
            node(id: "%s", controller_address: "%s"){
            verbose_name
            status
            datacenter {
                id
            }
            cpu_count
            memory_count
            management_ip
            }
            }
            """ % (node['id'], node['controller']['address'])

            executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)
            assert node['verbose_name'] == executed['node']['verbose_name']


@pytest.mark.asyncio
async def test_request_datapools(fixt_db, fixt_auth_context):  # noqa
    """Request datapools data"""
    list = ["verbose_name", "type", "vdisk_count", "iso_count", "file_count", "used_space", "free_space", "status"]
    for ordering in list:
        qu = """
        {
            datapools (ordering: "%s"){
                used_space,
                free_space,
                size,
                status,
                type,
                vdisk_count,
                file_count,
                iso_count,
                verbose_name,
            }
        }
        """ % ordering
        executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa


@pytest.mark.asyncio
async def test_types(fixt_db, fixt_controller, fixt_user_admin, fixt_create_automated_pool, fixt_auth_context):  # noqa
    # Получаем pool_id из динамической фикстуры пула
    pool_id = await Pool.select('id').gino.scalar()
    pool = await Pool.get(pool_id)

    controller_id = await Controller.select('id').gino.scalar()
    controller = await Controller.get(controller_id)

    qu = """{
            node(id: "%s", controller_address: "%s"){
                  verbose_name
                  status
                  datacenter {
                    id
                  }
                      cpu_count
                      memory_count
                      management_ip
                }
            }
        """ % (pool.node_id, controller.address)

    executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa

    qu = """{
            cluster(id: "%s", controller_address: "%s"){
              verbose_name
                }
            }
        """ % (pool.cluster_id, controller.address)

    executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa

    qu = """{
            datapool(id: "%s", controller_address: "%s"){
              verbose_name
              size
                  status
                  type
                  free_space
                }
            }
        """ % (pool.datapool_id, controller.address)

    executed = await execute_scheme(resources_schema, qu, context=fixt_auth_context)  # noqa
