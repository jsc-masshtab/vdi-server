# -*- coding: utf-8 -*-
import asyncio

from common.database import start_gino, stop_gino

from ws_listener_worker.resources_monitor_manager import ResourcesMonitorManager
from ws_listener_worker.thin_client_conn_monitor import ThinClientConnMonitor

from common.veil.veil_redis import REDIS_POOL
from common.languages import lang_init
from common.settings import DEBUG
from common.log.journal import system_logger
from common.utils import init_exit_handler

_ = lang_init()


def main():
    init_exit_handler()

    loop = asyncio.get_event_loop()
    loop.set_debug(DEBUG)  # debug mode

    # init gino
    loop.run_until_complete(start_gino())

    resources_monitor_manager = ResourcesMonitorManager()
    loop.create_task(resources_monitor_manager.listen_for_messages())

    thin_client_conn_monitor = ThinClientConnMonitor()
    loop.create_task(thin_client_conn_monitor.check_thin_client_connections())

    loop.run_forever()  # run until event loop stops

    system_logger._debug("Ws listener worker stopped")
    # free resources
    loop.run_until_complete(resources_monitor_manager.stop())
    REDIS_POOL.disconnect()
    loop.run_until_complete(stop_gino())


if __name__ == "__main__":
    main()
