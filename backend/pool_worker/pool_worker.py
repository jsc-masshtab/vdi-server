# -*- coding: utf-8 -*-
import asyncio


from database import start_gino, stop_gino

from redis_broker import REDIS_POOL

from languages import lang_init
from journal.log.logging import Logging
from journal.journal import Log

from common.utils import init_exit_handler

from pool_task_manager import PoolTaskManager
from vm_manager import VmManager

_ = lang_init()


def main():
    Logging.init_logging(True)
    init_exit_handler()

    loop = asyncio.get_event_loop()

    # init gino
    loop.run_until_complete(start_gino())

    pool_task_manager = PoolTaskManager()
    loop.create_task(pool_task_manager.start())

    vm_manager = VmManager()
    loop.create_task(vm_manager.start())

    loop.run_forever()  # run until event loop stop

    Log.general(_("Pool worker stopped"))

    REDIS_POOL.disconnect()
    loop.run_until_complete(stop_gino())


if __name__ == '__main__':
    main()
