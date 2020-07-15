# -*- coding: utf-8 -*-
import asyncio
# import time

from database import start_gino, stop_gino

import json

from redis_broker import POOL_TASK_QUEUE, REDIS_POOL, a_redis_lpop

from languages import lang_init
from journal.log.logging import Logging
from journal.journal import Log

from common.utils import init_exit_handler

from pool_task_manager import PoolTaskManager
from vm_manager import VmManager

_ = lang_init()


async def start_work():
    # Create PoolTaskManager
    pool_task_manager = PoolTaskManager()
    await pool_task_manager.start()

    # main loop. Await for work
    Log.general(_('Pool worker: start loop now'))
    while True:
        try:
            # wait for task message
            redis_data = await a_redis_lpop(POOL_TASK_QUEUE)
            Log.debug('PoolWorker start_work redis_data {}'.format(redis_data))
            task_data_dict = json.loads(redis_data.decode())

            await pool_task_manager.launch_task(task_data_dict)

        except asyncio.CancelledError:
            raise
        except Exception as ex:
            await Log.error('exception:' + str(ex))


def main():
    Logging.init_logging(True)
    init_exit_handler()

    loop = asyncio.get_event_loop()

    # init gino
    loop.run_until_complete(start_gino())

    # task request listener
    loop.create_task(start_work())

    # todo: Ввести команды отменить задачи/возобновить задачи и слушать эти команды.

    vm_manager = VmManager()
    loop.create_task(vm_manager.start())

    loop.run_forever()  # run until event loop stop

    Log.general(_("Pool worker stopped"))

    REDIS_POOL.disconnect()
    loop.run_until_complete(stop_gino())


if __name__ == '__main__':
    main()
