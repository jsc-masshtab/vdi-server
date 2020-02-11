# -*- coding: utf-8 -*-
import pytest

from tests.utils import execute_scheme
from tests.fixtures import fixt_db, auth_context_fixture  # noqa

from vm.schema import vm_schema


pytestmark = [pytest.mark.vms]


@pytest.mark.asyncio
async def test_request_vms(fixt_db, auth_context_fixture):  # noqa
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
    executed = await execute_scheme(vm_schema, qu, context=auth_context_fixture)  # noqa


@pytest.mark.asyncio
async def test_request_templates(fixt_db, auth_context_fixture):  # noqa
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
    executed = await execute_scheme(vm_schema, qu, context=auth_context_fixture)  # noqa
