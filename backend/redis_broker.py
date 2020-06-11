# -*- coding: utf-8 -*-

# import aioredis   # TODO: переехать на aioredis
import asyncio
from functools import wraps
from enum import Enum
import json
import uuid

import redis
import settings

from languages import lang_init
from journal.journal import Log as log


_ = lang_init()


REDIS_ASYNC_TIMEOUT = 0.02

POOL_TASK_QUEUE = 'POOL_TASK_QUEUE'
POOL_TASK_RESULT_CHANNEL = 'POOL_TASK_RESULT_CHANNEL'


class PoolTaskType(Enum):

    CREATING = 'CREATING'
    EXPANDING = 'EXPANDING'
    DELETING = 'DELETING'
    # DECREASING = 'DECREASING'


REDIS_POOL = redis.ConnectionPool.from_url(
    getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
    socket_connect_timeout=getattr(settings, 'REDIS_TIMEOUT', 5))

REDIS_CLIENT = redis.Redis(connection_pool=REDIS_POOL)

# провряем доступность Redis
REDIS_CLIENT.info()
# except ConnectionError:
#     raise


# def redis_error_handle(func):
#     """
#     Декоратор обеспечивает перехват исключений,
#     вызванных при взаимодействии с Redis.
#     """
#
#     @wraps(func)
#     def wrapped_function(*args, **kwargs):
#         """Декорируемая функция"""
#         response = None
#         try:
#             response = func(*args, **kwargs)
#         except redis.RedisError as error:
#             log.error(_("Redis error: %(error)s"), {'error': error})
#         return response
#
#     return wrapped_function


def get_thin_clients_count():
    numsub = REDIS_CLIENT.pubsub_numsub(settings.REDIS_THIN_CLIENT_CHANNEL)

    if isinstance(numsub, list):
        channel_count = numsub[0]
        if isinstance(channel_count, tuple):
            channel_count = channel_count[1]
        else:
            channel_count = 0
    else:
        channel_count = 0

    return channel_count


def save_license_dict(dict_name, data):
    for value in data:
        data[value] = str(data[value])
    return REDIS_CLIENT.hmset(dict_name, data)


def read_license_dict(dict_name):
    data = REDIS_CLIENT.hgetall(dict_name)
    read_dict = {key.decode('utf-8'): value.decode('utf-8') for (key, value) in data.items()}
    for value in read_dict:
        if read_dict[value] == 'None':
            read_dict[value] = None
        elif read_dict[value] == 'True':
            read_dict[value] = True
        elif read_dict[value] == 'False':
            read_dict[value] = False
        elif read_dict[value].isdigit():
            read_dict[value] = int(read_dict[value])
    return read_dict


async def a_redis_lpop(list_name):
    """asynchronous redis lpop. Wait until non-nill data received"""
    while True:
        data = REDIS_CLIENT.lpop(list_name)
        if data:
            return data
        await asyncio.sleep(REDIS_ASYNC_TIMEOUT)


async def a_redis_wait_for_message(self, redis_channel, predicate, timeout):
    """
    Asynchronously wait for message until timeout reached.

    :param predicate:  condition to find required message. Signature: def fun(json_message) -> bool
    :param timeout: time to wait. seconds
    :return bool: return true if awaited message received. Return false if timeuot expired and
     awaited message is not received
    """
    await_time = 0
    redis_subscriber = REDIS_CLIENT.pubsub()
    redis_subscriber.subscribe(redis_channel)

    while True:
        # try to receive message
        redis_message = redis_subscriber.get_message()

        if redis_message:
            json_message = redis_message['data'].decode()
            if predicate(json_message):
                return True

        # stop if time expired
        if await_time >= timeout:
            return False

        # count time
        await_time += REDIS_ASYNC_TIMEOUT
        await asyncio.sleep(REDIS_ASYNC_TIMEOUT)


def request_to_execute_pool_task(pool_id, pool_task_type):
    """Send request to pool worker to execute a task"""
    uuid_str = str(uuid.uuid4())
    data = {'task_id': uuid_str, 'task_type': pool_task_type, 'pool_id': pool_id}
    REDIS_CLIENT.rpush(POOL_TASK_QUEUE, json.dumps(data))
