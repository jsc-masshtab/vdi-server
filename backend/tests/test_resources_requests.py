import pytest

from graphene.test import Client

from controller_resources.schema import resources_schema

from utils import execute_scheme
from fixtures import fixt_db


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
    assert executed['clusters']
