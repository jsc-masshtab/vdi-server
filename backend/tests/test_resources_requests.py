import pytest

from graphene.test import Client  # noqa

from tests.utils import execute_scheme
from tests.fixtures import fixt_db, auth_context_fixture  # noqa

from controller_resources.schema import resources_schema


pytestmark = [pytest.mark.resources]


@pytest.mark.asyncio
async def test_request_clusters(fixt_db, auth_context_fixture):  # noqa
    """Request clusters data"""
    qu = """
    {
        clusters(ordering: "verbose_name"){
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
    """

    executed = await execute_scheme(resources_schema, qu, context=auth_context_fixture)  # noqa


@pytest.mark.asyncio
async def test_request_nodes(fixt_db, auth_context_fixture):  # noqa
    """Request nodes data"""
    qu = """
    {
        nodes(ordering: "-verbose_name"){
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
    """
    executed = await execute_scheme(resources_schema, qu, context=auth_context_fixture)

    # Чекним запрос определенного сервера (первого в списке), если серверы есть
    if executed['nodes']:
        print('__executed', executed)
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

        executed = await execute_scheme(resources_schema, qu, context=auth_context_fixture)
        assert node['verbose_name'] == executed['node']['verbose_name']


@pytest.mark.asyncio
async def test_request_datapools(fixt_db, auth_context_fixture):  # noqa
    """Request datapools data"""
    qu = """
    {
        datapools {
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
    """
    executed = await execute_scheme(resources_schema, qu, context=auth_context_fixture)  # noqa
