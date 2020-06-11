import asyncio
import signal

import redis
from redis import RedisError

import settings
from database import start_gino, stop_gino

import json

from redis_broker import POOL_TASK_QUEUE, PoolTaskType, REDIS_POOL, a_redis_lpop

from pool.models import AutomatedPool

from languages import lang_init
from journal.log.logging import Logging
from journal.journal import Log as log


from pool_task_manager import PoolTaskManager

_ = lang_init()


async def start_work():

    Logging.init_logging(True)
    # Create PoolTaskManager
    pool_task_manager = PoolTaskManager()

    # main loop. Await for work
    log.general(_('start loop now'))
    while True:
        try:
            # wait for task message
            data = await a_redis_lpop(POOL_TASK_QUEUE)
            queue, value = data
            json_data_dict = json.loads(value.decode())

            # get task data
            pool_id = json_data_dict['pool_id']
            pool_task_type = json_data_dict['task_type']

            # task execution
            native_loop = asyncio.get_event_loop()

            if pool_task_type == PoolTaskType.CREATING:
                automated_pool = await AutomatedPool.get(pool_id)
                # add data for protection
                pool_task_manager.add_new_pool_data(str(automated_pool.id), str(automated_pool.template_id))
                # start task
                pool_lock = pool_task_manager.get_pool_lock(pool_id)
                pool_lock.create_pool_task = native_loop.create_task(automated_pool.init_pool())

            elif pool_task_type == PoolTaskType.EXPANDING:
                pass

            elif pool_task_type == PoolTaskType.DELETING:
                pass

        except Exception as ex:
            # publish a message about unsuccesfull task if cant start it
            await log.error(ex)
            pass


if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    # init gino
    loop.run_until_complete(start_gino())

    try:
        loop.create_task(start_work())
        loop.run_forever()
    except KeyboardInterrupt:
        log.general(_("Pool worker interrupted"))
    finally:
        native_loop = asyncio.get_event_loop()
        native_loop.run_until_complete(stop_gino())
        REDIS_POOL.disconnect()
