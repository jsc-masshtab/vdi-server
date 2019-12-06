import pytest

from graphene.test import Client

from utils import execute_scheme
from fixtures import fixt_db

from controller_resources.schema import resources_schema


@pytest.mark.asyncio
async def test_request_clusters(fixt_db):

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

    executed = await execute_scheme(resources_schema, qu)


@pytest.mark.asyncio
async def test_request_nodes(fixt_db):

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
    executed = await execute_scheme(resources_schema, qu)

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

        executed = await execute_scheme(resources_schema, qu)
        print('___executed', executed)
        assert node['verbose_name'] == executed['node']['verbose_name']


@pytest.mark.asyncio
async def test_request_datapools(fixt_db):
    qu = """
    {
        datapools {     
            used_space      
            free_space      
            size      
            status      
            type      
            vdisk_count      
            file_count      
            iso_count      
            verbose_name    
        }   
    }
    """
    executed = await execute_scheme(resources_schema, qu)