# -*- coding: utf-8 -*-

import pytest
import json
import asyncio

from common.settings import PAM_AUTH, MINIMUM_SUPPORTED_DESKTOP_THIN_CLIENT_VERSION
from web_app.info.schema import broker_info_schema
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


pytestmark = [
    pytest.mark.tasks,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


@pytest.mark.asyncio
async def test_request_tasks(fixt_db, fixt_auth_context):  # noqa

    """Request broker info"""
    qu = """{
                minimum_supported_desktop_thin_client_version
         }"""
    executed = await execute_scheme(broker_info_schema, qu, context=fixt_auth_context)
    assert executed["minimum_supported_desktop_thin_client_version"] == MINIMUM_SUPPORTED_DESKTOP_THIN_CLIENT_VERSION
