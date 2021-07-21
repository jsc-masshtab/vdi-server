import pytest

from common.settings import PAM_AUTH

from web_app.tests.utils import execute_scheme
from web_app.tests.fixtures import (
    fixt_db,
    fixt_redis_client,
    fixt_controller,
    fixt_create_automated_pool,
    fixt_create_static_pool,  # noqa
    fixt_auth_context,
    fixt_group,
    fixt_user,
    fixt_user_admin,
    fixt_user_another_admin,  # noqa
    fixt_launch_workers,
    fixt_veil_client,
    get_resources_for_pool_test,
    get_auth_context,
)  # noqa
from web_app.settings.schema import settings_schema

pytestmark = [
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


@pytest.mark.asyncio
async def test_request_services(snapshot, fixt_db, fixt_auth_context):
    """Request services info"""
    qu = """{
            services{
                verbose_name
                status
            }
        }"""
    executed = await execute_scheme(settings_schema, qu, context=fixt_auth_context)
    snapshot.assert_match(executed)


@pytest.mark.asyncio
async def test_execute_service_action(fixt_db, fixt_auth_context):
    qu = """
        mutation{
            doServiceAction(sudo_password: "pass", service_name: "postgresql.service", 
                service_action: RESTART, check_errors:false)
                {ok}
        }
        """
    executed = await execute_scheme(settings_schema, qu, context=fixt_auth_context)
    assert executed["doServiceAction"]["ok"]