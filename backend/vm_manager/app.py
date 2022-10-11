# -*- coding: utf-8 -*-
import asyncio

from vm_manager.vm_manager_ import VmManager

from common.database import start_gino, stop_gino
from common.log.journal import system_logger
from common.settings import DEBUG
from common.single_instance_locker import SingleInstanceLocker
from common.utils import init_exit_handler
from common.veil.veil_redis import redis_deinit, redis_init


def main():
    init_exit_handler()
    loop = asyncio.get_event_loop()
    loop.set_debug(DEBUG)  # debug mode

    redis_init()

    single_instance_locker = SingleInstanceLocker("vm_manager_instance_lock")
    loop.run_until_complete(single_instance_locker.lock())

    # init gino
    loop.run_until_complete(start_gino())

    vm_manager = VmManager()
    loop.create_task(vm_manager.start())

    loop.run_forever()  # run until event loop stops

    system_logger._debug("Vm manager stopped")

    loop.run_until_complete(stop_gino())

    loop.run_until_complete(redis_deinit())


if __name__ == "__main__":
    main()
