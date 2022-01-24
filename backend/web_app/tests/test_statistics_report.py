# -*- coding: utf-8 -*-
import pytest
from web_app.tests.utils import execute_scheme
from web_app.statistics.schema import statistics_schema
from web_app.tests.fixtures import fixt_db, fixt_redis_client, fixt_user_admin, fixt_auth_context  # noqa
from common.settings import PAM_AUTH

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


async def test_group_list(snapshot, fixt_db, fixt_auth_context):  # noqa
    query = """{
        web_statistics_report(month:11, year:2022)
    }"""
    executed = await execute_scheme(statistics_schema, query, context=fixt_auth_context)
    snapshot.assert_match(executed)
