import pytest

from vdi.graphql_api import schema


@pytest.mark.asyncio
async def test_request_controllers_info():
    qu = """{
      controllers{
        ip
        clusters{
          verbose_name
          nodes{
            verbose_name
            datapools{
              verbose_name
            }
            templates{
              name
            }
          }
        }
      }
    }"""
    await schema.exec(qu)