import pytest

from common.log.journal import send_mail_async
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
                {ok, service_status}
        }
        """
    executed = await execute_scheme(settings_schema, qu, context=fixt_auth_context)
    assert executed["doServiceAction"]["ok"]
    assert executed["doServiceAction"]["service_status"] == "running"


@pytest.mark.asyncio
async def test_request_system_info(snapshot, fixt_db, fixt_auth_context):
    qu = """{
             system_info{
                 networks_list{
                     name
                     ipv4
                 }
                 time_zone
                 local_time
                 }
    }"""
    executed = await execute_scheme(settings_schema, qu, context=fixt_auth_context)
    assert executed["system_info"]["time_zone"]
    assert executed["system_info"]["local_time"]


@pytest.mark.asyncio
async def test_smtp_sending(snapshot, fixt_db, fixt_user_admin, fixt_auth_context):
    #  тестовая почта на яндексе: vdi.mashtab@yandex.ru - Bazalt1!
    qu = """
            mutation{
                changeSmtpSettings(hostname: "smtp.yandex.ru", 
                                   port: 465, 
                                   SSL: true,
                                   TLS: false,
                                   user: "vdi.mashtab@yandex.ru", 
                                   from_address: "vdi.mashtab@yandex.ru", 
                                   password: "Bazalt1!", 
                                   level: 2)
                    {ok}
            }
         """
    executed = await execute_scheme(settings_schema, qu, context=fixt_auth_context)

    qu = """{
            smtp_settings {
                  hostname
                  port
                  SSL
                  TLS
                  from_address
                  user
                  password
                  level
                 }
         }"""

    executed = await execute_scheme(settings_schema, qu, context=fixt_auth_context)
    snapshot.assert_match(executed)

    await send_mail_async(event_type=2, subject="Test smtp from VDI", message="TEST MESSAGE")
    assert True

    qu = """
            mutation{
                changeSmtpSettings(level: 4)
                    {ok}
            }
         """
    executed = await execute_scheme(settings_schema, qu, context=fixt_auth_context)
