# -*- coding: utf-8 -*-
import asyncio
import json
import weakref
from enum import Enum
from functools import wraps

from yaaredis import StrictRedis
from yaaredis.exceptions import ConnectionError, RedisError

import common.settings as settings
from common.languages import _local_
from common.subscription_sources import VDI_TASKS_SUBSCRIPTION, WsMessageType
from common.utils import gino_model_to_json_serializable_dict


class PoolWorkerCmd(Enum):

    CANCEL_TASK = "CANCEL_TASK"
    RESUME_TASK = "RESUME_TASK"


class WsMonitorCmd(Enum):

    ADD_CONTROLLER = "ADD_CONTROLLER"
    REMOVE_CONTROLLER = "REMOVE_CONTROLLER"
    RESTART_MONITOR = "RESTART_MONITOR"


class ThinClientCmd(Enum):
    DISCONNECT = "DISCONNECT"


class VeilRedisSubscriber:
    """Подписчик на события, получаемые клиентом редиса."""

    def __init__(self, channels, client):
        self.channels = channels
        self._weak_ref_to_client = weakref.ref(client)  # держим ссылку для авто отписки в __exit__
        self._msg_queue = asyncio.Queue(maxsize=1000)

        client.add_subscriber(subscriber=self)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        client = self._weak_ref_to_client()
        if client is not None:
            client.remove_subscriber(subscriber=self)

    def put_msg(self, redis_message):
        self._msg_queue.put_nowait(redis_message)

    async def get_msg(self):
        msg = await self._msg_queue.get()
        return msg


class VeilRedisClient(StrictRedis):
    """Клиент редиса."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.redis_receiving_messages_cor = None
        self._subscribers = []  # list of VeilRedisSubscribers

    def create_subscriber(self, channels):
        subscriber = VeilRedisSubscriber(channels=channels, client=self)
        return subscriber

    def add_subscriber(self, subscriber):
        self._subscribers.append(subscriber)

    def remove_subscriber(self, subscriber):
        self._subscribers.remove(subscriber)

    def send_message_to_subscribers(self, channel, redis_message):
        """Сообщения передаются в очереди подписчиков в текущем процессе."""
        for subscriber in self._subscribers:
            if channel in subscriber.channels:
                try:
                    subscriber.put_msg(redis_message)
                except asyncio.QueueFull:
                    pass


# глобальный обьект клиента редис
A_REDIS_CLIENT = None


def redis_init():
    global A_REDIS_CLIENT
    A_REDIS_CLIENT = VeilRedisClient(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                                     db=settings.REDIS_DB, password=settings.REDIS_PASSWORD,
                                     max_connections=settings.REDIS_MAX_CLIENT_CONN)

    loop = asyncio.get_event_loop()
    A_REDIS_CLIENT.redis_receiving_messages_cor = loop.create_task(redis_receiving_messages())


async def redis_deinit():
    global A_REDIS_CLIENT
    if A_REDIS_CLIENT.redis_receiving_messages_cor:
        A_REDIS_CLIENT.redis_receiving_messages_cor.cancel()
        A_REDIS_CLIENT.redis_receiving_messages_cor = None
    del A_REDIS_CLIENT  # В доке не нашел описания способа релиза ресурсов. Судя по всему это происходит автоматом
    # во время разрушения объекта.


def redis_get_subscriber(channels):
    return A_REDIS_CLIENT.create_subscriber(channels)


def redis_get_pubsub():
    return A_REDIS_CLIENT.pubsub()


async def redis_receiving_messages():
    """Получение сообщений от редиса.

    Получаем сообщния в одном месте в текущем процессе и затем раздаем их желающим
    в очереди. Сделано так для того, чтобы не приходилось подключаться к редису для каждого тонкого клиета.
    (Множество подключений - это во-первых многократный дубляж запрашиваемой информации, во-вторых
    вероятность превысить лимит максимального числа открытых файлов)
    """
    pubsub = redis_get_pubsub()
    await pubsub.subscribe(settings.INTERNAL_EVENTS_CHANNEL,
                           settings.WS_MONITOR_CHANNEL_OUT,
                           settings.REDIS_TEXT_MSG_CHANNEL,
                           settings.REDIS_THIN_CLIENT_CMD_CHANNEL)

    while True:
        try:
            redis_message = await redis_block_get_message(pubsub)
            channel = redis_message.get("channel").decode()
            if channel is None:
                continue

            A_REDIS_CLIENT.send_message_to_subscribers(channel, redis_message)
        except asyncio.CancelledError:
            pubsub.reset()
            break
        except Exception as e:
            from common.log.journal import system_logger
            await system_logger.error(
                message="Unexpected error in redis message receiving",
                description=str(e),
            )


async def redis_breconnect(connection):
    """Try to reconnect to redis server."""
    while True:
        try:
            await connection.connect()
            break
        except ConnectionError:
            # Таймаут чтобы не спамить попытки реконнекта
            await asyncio.sleep(settings.REDIS_RECONNECT_TIMEOUT)


async def redis_block_get_message(pubsub):
    while True:
        try:
            message = await pubsub.get_message()
            if message:
                return message
            await asyncio.sleep(settings.REDIS_ASYNC_TIMEOUT)
        except ConnectionError:
            await redis_breconnect(pubsub.connection)


async def redis_blpop(redis_list_name):
    while True:
        try:
            data = await A_REDIS_CLIENT.lpop(redis_list_name)
            if data:
                return data
            await asyncio.sleep(settings.REDIS_ASYNC_TIMEOUT)
        except ConnectionError:
            # При отсутствии соединения реконнект происходит под капотом в lpop
            # Поэтому идем к следующей итерации после таймаута
            await asyncio.sleep(settings.REDIS_RECONNECT_TIMEOUT)


async def redis_flushall():
    await A_REDIS_CLIENT.flushdb()


def redis_get_lock(name, timeout, blocking_timeout):
    return A_REDIS_CLIENT.lock(name=name, timeout=timeout, blocking_timeout=blocking_timeout)


def redis_error_handle(func):
    """Декоратор обеспечивает перехват исключений, вызванных при взаимодействии с Redis."""

    @wraps(func)
    def wrapped_function(*args, **kwargs):
        """Декорируемая функция."""
        response = None
        try:
            response = func(*args, **kwargs)
        except RedisError as error:
            from common.log.journal import system_logger

            system_logger._debug("Redis error {}".format(str(error)))
        return response

    return wrapped_function


async def save_license_dict(dict_name, data):
    for value in data:
        data[value] = str(data[value])
    return await A_REDIS_CLIENT.hmset(dict_name, data)


async def read_license_dict(dict_name):
    data = await A_REDIS_CLIENT.hgetall(dict_name)
    read_dict = {
        key.decode("utf-8"): value.decode("utf-8") for (key, value) in data.items()
    }
    for value in read_dict:
        if read_dict[value] == "None":
            read_dict[value] = None
        elif read_dict[value] == "True":
            read_dict[value] = True
        elif read_dict[value] == "False":
            read_dict[value] = False
        elif read_dict[value].isdigit():
            read_dict[value] = int(read_dict[value])
    return read_dict


async def redis_wait_for_message(redis_channel, predicate):
    """Asynchronously wait for message.

    :param predicate: condition to find required message. Signature: def fun(redis_message) -> bool
    :return message: return message when awaited message received.
     Ожидание потенциально бесконечно.
    """
    with redis_get_subscriber([redis_channel]) as subscriber:

        while True:
            # try to receive message
            redis_message = await subscriber.get_msg()
            if (
                redis_message
                and redis_message.get("type") == "message"  # noqa: W503
                and predicate(redis_message)  # noqa: W503
            ):
                return redis_message


async def a_redis_wait_for_task_completion(task_id):
    """Ждем завершения таски и возвращаем статус с которым она завершилась.

    Считаем что задача завершилась если ее статус сменился на CANCELLED/FAILED/FINISHED
    Ожидание потенциально бесконечно. Использовть только с asyncio.wait_for.
    """
    from common.models.task import TaskStatus

    with redis_get_subscriber([settings.INTERNAL_EVENTS_CHANNEL]) as subscriber:
        try:
            while True:
                # try to receive message
                redis_message = await subscriber.get_msg()
                if redis_message and redis_message["type"] == "message":

                    redis_message_data = redis_message["data"].decode()
                    redis_data_dict = json.loads(redis_message_data)

                    if (
                        redis_data_dict["resource"] == VDI_TASKS_SUBSCRIPTION
                        and redis_data_dict["event"] == "UPDATED"  # noqa: W503
                        and redis_data_dict["id"] == str(task_id)  # noqa: W503
                        and (  # noqa: W503
                            redis_data_dict["status"] == TaskStatus.CANCELLED.name
                            or redis_data_dict["status"]  # noqa: W503
                            == TaskStatus.FAILED.name  # noqa: W503
                            or redis_data_dict["status"]  # noqa: W503
                            == TaskStatus.FINISHED.name  # noqa: W503
                        )
                    ):

                        return redis_data_dict["status"]

        except asyncio.TimeoutError:
            raise
        except asyncio.CancelledError:
            raise
        except Exception as ex:  # noqa
            from common.log.journal import system_logger

            await system_logger.error(
                message=_local_("Redis task waiting exception."), description=str(ex)
            )

        return None


async def wait_for_task_result(task_id, wait_timeout):
    """Ждем результат задачи и возвращаем ее статус либо None если не дождались."""
    try:
        task_status = await asyncio.wait_for(
            a_redis_wait_for_task_completion(task_id), wait_timeout
        )
        return task_status
    except asyncio.TimeoutError:
        return None


async def request_to_execute_pool_task(entity_id, task_type, **additional_data):
    """Send request to task worker to execute a task. Return task id."""
    from common.models.task import Task

    task = await Task.soft_create(entity_id=entity_id, task_type=task_type.name,
                                  creator=additional_data.get("creator", "system"))
    task_id = str(task.id)
    data = {"task_id": task_id, "task_type": task_type.name, **additional_data}
    await A_REDIS_CLIENT.rpush(settings.POOL_TASK_QUEUE, json.dumps(data))
    return task.id


async def execute_delete_pool_task(
    pool_id: str, full, wait_for_result=True, wait_timeout=20, creator=None
):
    """Удаление автоматического пула.

    Если wait_for_result == True, то ждем результат.
    Возврщаем bool успешно или нет прошло удаление.
    """
    from common.models.task import PoolTaskType, TaskStatus  # для избежания цикл ссылки

    # send command to pool worker
    task_id = await request_to_execute_pool_task(
        pool_id, PoolTaskType.POOL_DELETE, full_deletion=full, creator=creator)

    # wait for result
    if wait_for_result:
        status = await wait_for_task_result(task_id, wait_timeout)
        return status and (status == TaskStatus.FINISHED.name)


async def send_cmd_to_cancel_tasks(task_ids: list, cancel_all=False):
    """Send command CANCEL_TASK to pool worker. Чтобы отменить все таски послать пустой список и cancel_all=True."""
    cmd_dict = {
        "command": PoolWorkerCmd.CANCEL_TASK.name,
        "task_ids": task_ids,
        "cancel_all": cancel_all,
    }
    await A_REDIS_CLIENT.rpush(settings.POOL_WORKER_CMD_QUEUE, json.dumps(cmd_dict))


async def send_cmd_to_cancel_tasks_associated_with_controller(
    controller_id, wait_for_result=False, wait_timeout=2
):
    """Send command CANCEL_TASK to pool worker.

    It will cancel all tasks associated with controller and will wait for cancellation if wait_for_result==True.
    """
    #  Send cmd
    cmd_dict = {
        "command": PoolWorkerCmd.CANCEL_TASK.name,
        "controller_id": str(controller_id),
        "resumable": True,
    }
    await A_REDIS_CLIENT.rpush(settings.POOL_WORKER_CMD_QUEUE, json.dumps(cmd_dict))

    #  Wait for result
    if wait_for_result:
        from common.models.task import Task, TaskStatus

        tasks_to_cancel = await Task.get_ids_of_tasks_associated_with_controller(
            controller_id, TaskStatus.IN_PROGRESS
        )
        await asyncio.gather(
            *[wait_for_task_result(task, wait_timeout) for task in tasks_to_cancel]
        )


async def send_cmd_to_cancel_tasks_associated_with_entity(entity_id):
    """Cancel all tasks associated with entity."""
    #  Send cmd
    cmd_dict = {
        "command": PoolWorkerCmd.CANCEL_TASK.name,
        "entity_id": str(entity_id),
        "resumable": True,
    }
    await A_REDIS_CLIENT.rpush(settings.POOL_WORKER_CMD_QUEUE, json.dumps(cmd_dict))


async def send_cmd_to_resume_tasks_associated_with_controller(controller_id):
    """Command to pool worker to resume tasks."""
    cmd_dict = {
        "command": PoolWorkerCmd.RESUME_TASK.name,
        "controller_id": str(controller_id),
    }
    await A_REDIS_CLIENT.rpush(settings.POOL_WORKER_CMD_QUEUE, json.dumps(cmd_dict))


async def send_cmd_to_ws_monitor(controller_id, ws_monitor_cmd: WsMonitorCmd):
    """Send command to ws monitor."""
    cmd_dict = {"controller_id": str(controller_id), "command": ws_monitor_cmd.name}
    await A_REDIS_CLIENT.rpush(settings.WS_MONITOR_CMD_QUEUE, json.dumps(cmd_dict))


async def publish_to_redis(channel, message):
    try:
        await A_REDIS_CLIENT.publish(channel, message)
    except RedisError as error:
        from common.log.journal import system_logger
        system_logger._debug("Redis error {}".format(str(error)))


async def publish_data_in_internal_channel(resource_type: str, event_type: str,
                                           model, additional_data: dict = None, description: str = None):
    """Publish db model data in redis channel INTERNAL_EVENTS_CHANNEL."""
    msg_dict = dict(
        resource=resource_type,
        msg_type=WsMessageType.DATA.value,
        event=event_type,
        description=description
    )

    msg_dict.update(gino_model_to_json_serializable_dict(model))
    if additional_data:
        msg_dict.update(additional_data)
    await publish_to_redis(settings.INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))
