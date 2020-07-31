# -*- coding: utf-8 -*-
import asyncio


from common.database import start_gino, stop_gino
from common.veil.veil_redis import REDIS_POOL

from common.languages import lang_init
from common.log.journal import system_logger
from common.utils import init_exit_handler

from pool_worker.pool_task_manager import PoolTaskManager
from pool_worker.vm_manager import VmManager

_ = lang_init()


def main():
    init_exit_handler()

    loop = asyncio.get_event_loop()

    # init gino
    loop.run_until_complete(start_gino())

    pool_task_manager = PoolTaskManager()
    loop.create_task(pool_task_manager.start())

    vm_manager = VmManager()
    loop.create_task(vm_manager.start())

    loop.run_forever()  # run until event loop stop

    system_logger._debug("Pool worker stopped")

    REDIS_POOL.disconnect()
    loop.run_until_complete(stop_gino())


if __name__ == '__main__':
    main()
