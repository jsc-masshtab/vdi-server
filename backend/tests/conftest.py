# -*- coding: utf-8 -*-
"""Common fixtures."""

import asyncio
import pytest
from app import start_gino, stop_gino

from resources_monitoring.resources_monitor_manager import resources_monitor_manager


@pytest.fixture(scope="session", autouse=True)
def resource_monitor_manager_fixture(request):
    """Запускается перед первым тестом и завершается после последнего."""
    loop = asyncio.get_event_loop()

    async def setup():
        await start_gino()
        await resources_monitor_manager.start()
    loop.run_until_complete(setup())

    def teardown():
        async def a_teardown():
            try:
                await resources_monitor_manager.stop()
                await stop_gino()
            except:  # noqa
                pass

        loop.run_until_complete(a_teardown())

    request.addfinalizer(teardown)
    return True
