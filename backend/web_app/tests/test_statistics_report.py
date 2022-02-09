# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime, timedelta
import json
import pytest

from common.database import db

from tornado.testing import gen_test

from web_app.tests.utils import execute_scheme
from web_app.statistics.schema import statistics_schema
from web_app.tests.fixtures import (
    fixt_db,  # noqa: F401
    fixt_redis_client,
    fixt_user_locked,  # noqa: F401
    fixt_user,  # noqa: F401
    fixt_user_admin,  # noqa: F401
    fixt_auth_dir,  # noqa: F401
    fixt_mapping,  # noqa: F401
    fixt_launch_workers,  # noqa
    fixt_group,  # noqa: F401
    fixt_group_role,  # noqa: F401
    fixt_create_static_pool,  # noqa: F401
    fixt_controller,  # noqa: F401
    fixt_veil_client,  # noqa: F401
    get_auth_context,  # noqa: F401
    several_static_pools,  # noqa: F401
    several_static_pools_with_user,  # noqa: F401
    fixt_auth_context,  # noqa
    get_auth_context
)
from web_app.tests.utils import VdiHttpTestCase
from common.models.active_tk_connection import ActiveTkConnection, TkConnectionEvent
from common.models.auth import User
from common.models.pool import Pool
from common.models.vm import Vm
from common.settings import PAM_AUTH

from common.subscription_sources import WsMessageType

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


async def test_web_statistics_report(snapshot, fixt_db, fixt_auth_context):  # noqa
    query = """{
        web_statistics_report(month:11, year:2022)
    }"""
    executed = await execute_scheme(statistics_schema, query, context=fixt_auth_context)
    snapshot.assert_match(executed)


class TestPoolStatistics(VdiHttpTestCase):

    @pytest.mark.usefixtures("fixt_db", "fixt_user", "fixt_create_static_pool")
    @gen_test
    async def test_pools_statistics_ok(self):
        # clear all
        await db.status(db.text("TRUNCATE TABLE active_tk_connection CASCADE;"))

        # login
        (user_name, access_token) = await self.do_login(user_name="test_user", password="veil")

        # connect to ws
        ws_client = await self.connect_to_thin_client_ws(access_token)
        assert ws_client

        pool = await Pool.query.where(Pool.pool_type == Pool.PoolTypes.STATIC).gino.first()
        vm_id = await Vm.select("id").where(Vm.pool_id == pool.id).gino.scalar()  # id ВМ, созданной в фикстуре

        try:
            # update (Эмулировать подключение к ВМ)
            update_data_dict = {
                "msg_type": WsMessageType.UPDATED.value,
                "vm_id": str(vm_id),
                "event": TkConnectionEvent.VM_CONNECTED.value,
            }
            ws_client.write_message(json.dumps(update_data_dict))
            await asyncio.sleep(1)  # Подождем так как на update ответов не присылается

            # test statistics
            lst = datetime.now()
            fst = lst - timedelta(hours=24)
            qu = (
                """
                {
                  pool_usage_statistics(start_date: "%s", end_date: "%s", pool_id: "%s") {
                    successful_conn_number
                    disconn_number
                    conn_err_number
                    conn_duration_average
                    
                    conn_errors {
                      name
                      conn_number
                    }
                    
                    used_pools_overall {
                      name
                      conn_number
                    }
                    
                    used_client_os {
                      name
                      conn_number
                    }
                    
                    used_client_versions {
                      name
                      conn_number
                    }
                    
                    users {
                      name
                      conn_number
                    }
                             
                    conn_number_by_time_interval {
                      time_interval
                      conn_number
                      percentage
                    }
                  }
                }
                  """
                % (fst.replace(microsecond=0).isoformat(), lst.replace(microsecond=0).isoformat(), pool.id)
            )
            auth_context = await get_auth_context()
            executed = await execute_scheme(statistics_schema, qu, context=auth_context)
            assert executed["pool_usage_statistics"]["successful_conn_number"] == 1
            assert executed["pool_usage_statistics"]["conn_err_number"] == 0
            assert executed["pool_usage_statistics"]["used_pools_overall"][0]["name"] == pool.verbose_name
            assert executed["pool_usage_statistics"]["used_pools_overall"][0]["conn_number"] == 1
            assert executed["pool_usage_statistics"]["used_client_os"][0]["name"] == "Linux"
            assert executed["pool_usage_statistics"]["used_client_os"][0]["conn_number"] == 1
            assert executed["pool_usage_statistics"]["users"][0]["name"] == user_name
            assert executed["pool_usage_statistics"]["users"][0]["conn_number"] == 1
            assert executed["pool_usage_statistics"]["used_client_versions"][0]["name"] == "1.4.1"
            assert executed["pool_usage_statistics"]["used_client_versions"][0]["conn_number"] == 1

        except Exception:
            raise
        finally:
            # disconnect
            ws_client.close()
            await asyncio.sleep(0.1)
