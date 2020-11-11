# -*- coding: utf-8 -*-

# import aioredis   # TODO: переехать на aioredis
import asyncio
from enum import Enum
import json
import time
from functools import wraps

import redis

import common.settings
from common.languages import lang_init
# import common.models as models
from web_app.front_ws_api.subscription_sources import VDI_TASKS_SUBSCRIPTION


_ = lang_init()


# TODO: перенести в settings
REDIS_ASYNC_TIMEOUT = 0.01

# Pool worker related
POOL_TASK_QUEUE = 'POOL_TASK_QUEUE'  # Очередь задач пул воркера
POOL_WORKER_CMD_QUEUE = 'POOL_WORKER_CMD_QUEUE'  # Очередь для команд, которые принимаются пул воркером (Например,
# команда на отмену задачи)


class PoolWorkerCmd(Enum):

    CANCEL_TASK = 'CANCEL_TASK'
    RESUME_TASK = 'RESUME_TASK'


# Ws monitor related
WS_MONITOR_CHANNEL_OUT = 'WS_MONITOR_CHANNEL_OUT'  # по этому каналу сообщения полученные по ws от контроллеров
WS_MONITOR_CMD_QUEUE = 'WS_MONITOR_CMD_QUEUE'  # Очередь для команд, которые принимаются монитором ws. Переходим на
# очередь, чтобы гарантировать порядок команд


class WsMonitorCmd(Enum):

    ADD_CONTROLLER = 'ADD_CONTROLLER'
    REMOVE_CONTROLLER = 'REMOVE_CONTROLLER'
    RESTART_MONITOR = 'RESTART_MONITOR'


#
INTERNAL_EVENTS_CHANNEL = 'INTERNAL_EVENTS_CHANNEL'  # Канал для внутренних событий vdi


REDIS_POOL = redis.ConnectionPool.from_url(
    getattr(common.settings, 'REDIS_URL', 'redis://localhost:6379/0'),
    socket_connect_timeout=getattr(common.settings, 'REDIS_TIMEOUT', 5))

REDIS_CLIENT = redis.Redis(connection_pool=REDIS_POOL)

# провряем доступность Redis
REDIS_CLIENT.info()
# except ConnectionError:
#     raise


def redis_error_handle(func):
    """
    Декоратор обеспечивает перехват исключений,
    вызванных при взаимодействии с Redis.
    """

    @wraps(func)
    def wrapped_function(*args, **kwargs):
        """Декорируемая функция"""
        response = None
        try:
            response = func(*args, **kwargs)
        except redis.RedisError as error:
            from common.log.journal import system_logger
            system_logger._debug('Redis error ', str(error))
        return response

    return wrapped_function


def get_thin_clients_count():
    numsub = REDIS_CLIENT.pubsub_numsub(common.settings.REDIS_THIN_CLIENT_CHANNEL)

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


async def a_redis_wait_for_message(redis_channel, predicate, timeout):
    """
    Asynchronously wait for message until timeout reached.

    :param predicate:  condition to find required message. Signature: def fun(redis_message) -> bool
    :param timeout: time to wait. seconds
    :return bool: return true if awaited message received. Return false if timeuot expired and
     awaited message is not received
    """
    redis_subscriber = REDIS_CLIENT.pubsub()
    redis_subscriber.subscribe(redis_channel)

    try:
        start_time = time.time()  # sec from epoch
        while True:
            # try to receive message
            redis_message = redis_subscriber.get_message()
            # if redis_message:
            #    print('redis_message ', redis_message)
            if redis_message and redis_message['type'] == 'message' and predicate(redis_message):
                return True

            # stop if time expired
            cur_time = time.time()
            if (cur_time - start_time) >= timeout:
                return False

            await asyncio.sleep(REDIS_ASYNC_TIMEOUT)

    except asyncio.CancelledError:  # Проброс необходим, чтобы корутина могла отмениться
        raise
    except Exception as ex:  # noqa
        from common.log.journal import system_logger
        await system_logger.error(message=_('Redis waiting exception.'), description=str(ex))

    return False


async def a_redis_get_message(redis_subscriber):
    """Asynchronously wait for message from channel"""
    while True:
        redis_message = redis_subscriber.get_message()
        if redis_message:
            return redis_message

        await asyncio.sleep(REDIS_ASYNC_TIMEOUT)


async def a_redis_wait_for_task_completion(task_id):
    """Ждем завершения таски и возвращаем статус с которым она завершилась
    Считаем что задача завершилась если ее статус сменился на CANCELLED/FAILED/FINISHED
    Ожидание потенциально бесконечно. Использовть только с asyncio.wait_for"""

    from common.models.task import TaskStatus

    redis_subscriber = REDIS_CLIENT.pubsub()
    redis_subscriber.subscribe(INTERNAL_EVENTS_CHANNEL)

    try:
        while True:
            # try to receive message
            redis_message = redis_subscriber.get_message()
            if redis_message and redis_message['type'] == 'message':

                redis_message_data = redis_message['data'].decode()
                redis_data_dict = json.loads(redis_message_data)

                if redis_data_dict['resource'] == VDI_TASKS_SUBSCRIPTION and \
                        redis_data_dict['event'] == 'status_changed' and \
                        redis_data_dict['task_id'] == str(task_id) and \
                        (redis_data_dict['task_status'] == TaskStatus.CANCELLED.name or  # noqa
                         redis_data_dict['task_status'] == TaskStatus.FAILED.name or  # noqa
                         redis_data_dict['task_status'] == TaskStatus.FINISHED.name):

                    return redis_data_dict['task_status']

            await asyncio.sleep(REDIS_ASYNC_TIMEOUT)

    except asyncio.TimeoutError:
        raise
    except asyncio.CancelledError:
        raise
    except Exception as ex:  # noqa
        from common.log.journal import system_logger
        await system_logger.error(message=_('Redis task waiting exception.'), description=str(ex))


async def wait_for_task_result(task_id, wait_timeout):
    """Ждем результат задачи и возвращаем ее статус либо None если не дождплись"""
    try:
        task_status = await asyncio.wait_for(a_redis_wait_for_task_completion(task_id), wait_timeout)
        return task_status
    except asyncio.TimeoutError:
        return None


async def request_to_execute_pool_task(entity_id, pool_task_type, **additional_data):
    """Send request to pool worker to execute a task. Return task id"""
    from common.models.task import Task
    task = await Task.create(entity_id=entity_id, task_type=pool_task_type)
    task_id = str(task.id)
    data = {'task_id': task_id, 'task_type': pool_task_type.name, **additional_data}
    REDIS_CLIENT.rpush(POOL_TASK_QUEUE, json.dumps(data))
    return task.id


async def execute_delete_pool_task(pool_id: str, full, wait_for_result=True, wait_timeout=20):
    """Удаление автоматического пула. Если wait_for_result == True, то ждем результат
    Возврщаем bool успешно или нет прошло удаление"""

    from common.models.task import PoolTaskType, TaskStatus  # для избежания цикл ссылки

    # send command to pool worker
    task_id = await request_to_execute_pool_task(pool_id, PoolTaskType.DELETING_POOL, deletion_full=full)

    # wait for result
    if wait_for_result:
        status = await wait_for_task_result(task_id, wait_timeout)
        return status and (status == TaskStatus.FINISHED.name)


@redis_error_handle
def send_cmd_to_cancel_tasks(task_ids: list, cancel_all=False):
    """Send command CANCEL_TASK to pool worker. Чтобы отменить все таски послать пустой список и cancel_all=True"""
    cmd_dict = {'command': PoolWorkerCmd.CANCEL_TASK.name, 'task_ids': task_ids, 'cancel_all': cancel_all}
    REDIS_CLIENT.rpush(POOL_WORKER_CMD_QUEUE, json.dumps(cmd_dict))


async def send_cmd_to_cancel_tasks_associated_with_controller(controller_id, wait_for_result=False, wait_timeout=2):
    """Send command CANCEL_TASK to pool worker. It will cancel all tasks associated with controller
    and will wait for cancellation if wait_for_result==True"""

    #  Send cmd
    cmd_dict = {'command': PoolWorkerCmd.CANCEL_TASK.name, 'controller_id': str(controller_id),
                'resumable': True}
    REDIS_CLIENT.rpush(POOL_WORKER_CMD_QUEUE, json.dumps(cmd_dict))

    #  Wait for result
    if wait_for_result:
        from common.models.task import Task
        tasks_to_cancel = await Task.get_ids_of_tasks_associated_with_controller(controller_id)
        await asyncio.gather(*[wait_for_task_result(task, wait_timeout) for task in tasks_to_cancel])


@redis_error_handle
def send_cmd_to_resume_tasks_associated_with_controller(controller_id):
    """Command to pool worker to resume tasks"""
    cmd_dict = {'command': PoolWorkerCmd.RESUME_TASK.name, 'controller_id': str(controller_id)}
    REDIS_CLIENT.rpush(POOL_WORKER_CMD_QUEUE, json.dumps(cmd_dict))


@redis_error_handle
def send_cmd_to_ws_monitor(controller_id, ws_monitor_cmd: WsMonitorCmd):
    """Send command to ws monitor"""
    cmd_dict = {'controller_id': str(controller_id), 'command': ws_monitor_cmd.name}
    REDIS_CLIENT.rpush(WS_MONITOR_CMD_QUEUE, json.dumps(cmd_dict))
