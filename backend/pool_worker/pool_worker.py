# -*- coding: utf-8 -*-
import asyncio

from database import start_gino, stop_gino

import json

from redis_broker import POOL_TASK_QUEUE, PoolTaskType, REDIS_POOL, a_redis_lpop

from languages import lang_init
from journal.log.logging import Logging
from journal.journal import Log as log


from pool_task_manager import PoolTaskManager

_ = lang_init()


async def start_work():

    Logging.init_logging(True)
    # Create PoolTaskManager
    pool_task_manager = PoolTaskManager()
    await pool_task_manager.fill_start_data()

    # main loop. Await for work
    log.general(_('Pool worker: start loop now'))
    while True:
        try:
            # wait for task message
            redis_data = await a_redis_lpop(POOL_TASK_QUEUE)
            # print('got redis_data: ', redis_data)
            task_data_dict = json.loads(redis_data.decode())

            # get task data
            pool_id = task_data_dict['pool_id']
            pool_task_type = task_data_dict['task_type']

            # task execution
            if pool_task_type == PoolTaskType.CREATING.name:
                await pool_task_manager.start_pool_initialization(pool_id)

            elif pool_task_type == PoolTaskType.EXPANDING.name:
                await pool_task_manager.start_pool_expanding(pool_id)

            elif pool_task_type == PoolTaskType.DELETING.name:
                full = task_data_dict['deletion_full']
                await pool_task_manager.start_pool_deleting(pool_id, full)

        except Exception as ex:
            await log.error(ex)
            pass


def main():
    loop = asyncio.get_event_loop()

    # init gino
    loop.run_until_complete(start_gino())

    try:
        loop.create_task(start_work())
        loop.run_forever()
    except KeyboardInterrupt:
        log.general(_("Pool worker interrupted"))
    finally:
        loop.run_until_complete(stop_gino())
        REDIS_POOL.disconnect()


if __name__ == '__main__':
    main()
