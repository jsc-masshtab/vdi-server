# -*- coding: utf-8 -*-
import asyncio

from common.database import start_gino, stop_gino
from common.log.journal import system_logger
from common.settings import DEBUG
from common.single_instance_locker import SingleInstanceLocker
from common.utils import init_exit_handler
from common.veil.veil_redis import redis_deinit, redis_init

from monitor_worker.resources_monitor_manager import ResourcesMonitorManager
from monitor_worker.thin_client_conn_monitor import ThinClientConnMonitor


def main():
    init_exit_handler()

    loop = asyncio.get_event_loop()
    loop.set_debug(DEBUG)  # debug mode

    redis_init()

    single_instance_locker = SingleInstanceLocker("monitor_worker_instance_lock")
    loop.run_until_complete(single_instance_locker.lock())

    # init gino
    loop.run_until_complete(start_gino())

    resources_monitor_manager = ResourcesMonitorManager()
    loop.create_task(resources_monitor_manager.listen_for_messages())

    thin_client_conn_monitor = ThinClientConnMonitor()
    thin_client_conn_monitor.start()

    loop.run_forever()  # run until event loop stops

    system_logger._debug("Ws listener worker stopped")
    # free resources
    loop.run_until_complete(resources_monitor_manager.stop())
    loop.run_until_complete(stop_gino())
    loop.run_until_complete(redis_deinit())


if __name__ == "__main__":
    main()
