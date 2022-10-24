# -*- coding: utf-8 -*-
import pytest

from web_app.gateway.gateway_connection import GatewayConnection
from web_app.tests.fixtures import (  # noqa: F401
    fixt_db,
    fixt_redis_client,
    fixt_create_static_pool,
    fixt_controller,
    fixt_veil_client,
    fixt_vm,
    fixt_vm_connection_data,
    fixt_active_tk_connection,
    fixt_user,
    several_static_pools,
    several_static_pools_with_user
)


pytestmark = [pytest.mark.asyncio, pytest.mark.gateway]


@pytest.mark.usefixtures(
    "fixt_db", "fixt_redis_client", "fixt_create_static_pool", "fixt_controller",
    "fixt_veil_client", "fixt_vm", "fixt_vm_connection_data", "fixt_active_tk_connection",
    "fixt_user", "several_static_pools", "several_static_pools_with_user"
)
class TestGateway:
    async def test_get_ports_in_use(self):
        gateway_connection = GatewayConnection()
        port = await gateway_connection.get_ports_in_use()
        assert len(port) == 1
        assert 3389 in port

    async def test_start_connections(self):
        gateway_connection = GatewayConnection()
        await gateway_connection.start_connections()
