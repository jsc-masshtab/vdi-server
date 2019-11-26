import pytest

from graphene.test import Client

from controller_resources.schema import resources_schema


def test_request_clusters():
    client = Client(resources_schema)

    # add controller
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

    executed = client.execute(qu)
    assert executed['clusters']