# -*- coding: utf-8 -*-
import asyncio

from common.database import start_gino, stop_gino
from common.log.journal import system_logger
from common.settings import DEBUG
from common.single_instance_locker import SingleInstanceLocker
from common.utils import init_exit_handler
from common.veil.veil_redis import redis_deinit, redis_init

from pool_worker.pool_task_manager import PoolTaskManager
from pool_worker.vm_manager import VmManager


def main():
    init_exit_handler()
    loop = asyncio.get_event_loop()
    loop.set_debug(DEBUG)  # debug mode

    redis_init()

    single_instance_locker = SingleInstanceLocker("pool_worker_instance_lock")
    loop.run_until_complete(single_instance_locker.lock())

    # init gino
    loop.run_until_complete(start_gino())

    pool_task_manager = PoolTaskManager()
    loop.create_task(pool_task_manager.start())

    vm_manager = VmManager()
    loop.create_task(vm_manager.start())

    loop.run_forever()  # run until event loop stops

    system_logger._debug("Pool worker stopped")

    loop.run_until_complete(stop_gino())

    loop.run_until_complete(single_instance_locker.unlock())

    loop.run_until_complete(redis_deinit())


if __name__ == "__main__":
    main()
