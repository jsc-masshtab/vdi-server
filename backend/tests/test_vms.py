import pytest

from tests.utils import execute_scheme
from tests.fixtures import fixt_db

from vm.schema import vm_schema


@pytest.mark.asyncio
@pytest.mark.vms
async def test_request_vms(fixt_db):
    qu = """
    {
        vms(ordering: "verbose_name"){
        verbose_name
        id
        
        template{
          verbose_name
        }
        management_ip
        status
        controller {
          address
        }
    }
    }
    """
    executed = await execute_scheme(vm_schema, qu)


@pytest.mark.asyncio
@pytest.mark.vms
async def test_request_templates(fixt_db):
    qu = """
    {
        templates{
            verbose_name
            controller{
              address
            }
        }
    }
    """
    executed = await execute_scheme(vm_schema, qu)
