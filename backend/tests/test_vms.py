import pytest

from tests.utils import execute_scheme
from tests.fixtures import fixt_db, auth_context_fixture

from vm.schema import vm_schema


@pytest.mark.asyncio
@pytest.mark.vms
async def test_request_vms(fixt_db, auth_context_fixture):
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
    executed = await execute_scheme(vm_schema, qu, context=auth_context_fixture)


@pytest.mark.asyncio
@pytest.mark.vms
async def test_request_templates(fixt_db, auth_context_fixture):
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
    executed = await execute_scheme(vm_schema, qu, context=auth_context_fixture)
