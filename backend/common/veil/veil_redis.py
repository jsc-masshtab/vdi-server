# -*- coding: utf-8 -*-
import asyncio
import json
import weakref
from enum import Enum
from functools import wraps

from yaaredis import StrictRedis
from yaaredis.exceptions import ConnectionError, LockError, RedisError

import common.settings as settings
from common.languages import _local_
from common.subscription_sources import VDI_TASKS_SUBSCRIPTION, WsEventToClient, WsMessageType
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


class ReacquireLock:

    def __init__(self, redis_client, lock_name):
        self._redis_client = redis_client
        self._lock_name = lock_name

        self._app_lock = None
        self._timeout = 30
        self._keep_reacquiring_task = None

    async def __aenter__(self):

        self._app_lock = self._redis_client.lock(name=self._lock_name, timeout=self._timeout)
        # Acquire lock and keep reacquiring
        await self._app_lock.acquire()

        loop = asyncio.get_event_loop()
        self._keep_reacquiring_task = loop.create_task(self._keep_reacquiring())

        return self._app_lock

    async def __aexit__(self, type, value, traceback):

        if self._keep_reacquiring_task:
            self._keep_reacquiring_task.cancel()
        if self._app_lock:
            try:
                await self._app_lock.release()
            except LockError:
                pass

    async def _keep_reacquiring(self):

        while True:
            await asyncio.sleep(self._timeout - 10)
            # print("Before self.reacquire()", flush=True)
            await self._redis_client.reacquire(self._app_lock)
            # print("After self.reacquire()", flush=True)


# Добавляем скрипт для для REACQUIRE, так как его нет в редис клиенте
# KEYS[1] - lock name
# ARGV[1] - token
# ARGV[2] - milliseconds
# return 1 if the locks time was reacquired, otherwise 0
LUA_REACQUIRE_SCRIPT = """
    local token = redis.call('get', KEYS[1])
    if not token or token ~= ARGV[1] then
        return 0
    end
    redis.call('pexpire', KEYS[1], ARGV[2])
    return 1
"""


class VeilRedisClient(StrictRedis):
    """Клиент редиса."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._subscribers = []  # list of VeilRedisSubscribers

        loop = asyncio.get_event_loop()
        self.redis_receiving_messages_cor = loop.create_task(self.redis_receiving_messages())

        # add reacquire support
        self._lua_reacquire = self.register_script(LUA_REACQUIRE_SCRIPT)

    async def reacquire(self, lock_obj):
        """Reset a TTL of an already acquired lock back to a timeout value."""
        if lock_obj.local.get() is None:
            raise LockError("Cannot reacquire an unlocked lock")
        if lock_obj.timeout is None:
            raise LockError("Cannot reacquire a lock with no timeout")

        timeout = int(lock_obj.timeout * 1000)
        if not bool(
            await self._lua_reacquire.execute(
                keys=[lock_obj.name],
                args=[lock_obj.local.get(), timeout],
                client=lock_obj.redis
            )
        ):
            raise LockError("Cannot extend a lock that's no longer owned")
        return True

    async def stop_redis_receiving_messages_cor(self):
        if self.redis_receiving_messages_cor:  # noqa
            self.redis_receiving_messages_cor.cancel()  # noqa
            # await self.redis_receiving_messages_cor()
            self.redis_receiving_messages_cor = None

    async def redis_receiving_messages(self):
        """Получение сообщений от редиса.

        Получаем сообщния в одном месте в текущем процессе и затем раздаем их желающим
        в очереди. Сделано так для того, чтобы не приходилось подключаться к редису для каждого тонкого клиета.
        (Множество подключений - это во-первых многократный дубляж запрашиваемой информации, во-вторых
        вероятность превысить лимит максимального числа открытых файлов)
        """
        pubsub = self.pubsub()
        await pubsub.subscribe(settings.INTERNAL_EVENTS_CHANNEL,
                               settings.WS_MONITOR_CHANNEL_OUT,
                               settings.REDIS_TEXT_MSG_CHANNEL,
                               settings.REDIS_THIN_CLIENT_CMD_CHANNEL,
                               settings.POOL_WORKER_CMD_CHANNEL)

        while True:
            try:
                redis_message = await self.redis_block_get_message(pubsub)
                channel = redis_message.get("channel").decode()
                if channel is None:
                    continue

                self.send_message_to_subscribers(channel, redis_message)
            except asyncio.CancelledError:
                pubsub.reset()
                break
            except Exception as e:
                from common.log.journal import system_logger
                await system_logger.error(
                    message="Unexpected error in redis message receiving",
                    description=str(e),
                )

    async def redis_block_get_message(self, pubsub):
        while True:
            try:
                message = await pubsub.get_message()
                if message:
                    return message
                await asyncio.sleep(settings.REDIS_ASYNC_TIMEOUT)
            except ConnectionError:
                await self.redis_breconnect(pubsub.connection)

    async def redis_breconnect(self, connection):
        """Try to reconnect to redis server."""
        while True:
            try:
                await connection.connect()
                break
            except ConnectionError:
                # Таймаут чтобы не спамить попытки реконнекта
                await asyncio.sleep(settings.REDIS_RECONNECT_TIMEOUT)

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

    async def get_value_with_def(self, key, value_type, default):
        value = await self.get(key)
        if value is None:
            return default

        value = value_type(value.decode("utf-8"))
        return value

    async def redis_blpop(self, redis_list_name):
        while True:
            try:
                data = await self.lpop(redis_list_name)
                if data:
                    return data
                await asyncio.sleep(settings.REDIS_ASYNC_TIMEOUT)
            except ConnectionError:
                # При отсутствии соединения реконнект происходит под капотом в lpop
                # Поэтому идем к следующей итерации после таймаута
                await asyncio.sleep(settings.REDIS_RECONNECT_TIMEOUT)

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


# глобальный обьект клиента редис
A_REDIS_CLIENT = None


def redis_init():
    global A_REDIS_CLIENT
    A_REDIS_CLIENT = VeilRedisClient(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                                     db=settings.REDIS_DB, password=settings.REDIS_PASSWORD,
                                     max_connections=settings.REDIS_MAX_CLIENT_CONN)


async def redis_deinit():
    global A_REDIS_CLIENT
    if A_REDIS_CLIENT:
        await A_REDIS_CLIENT.stop_redis_receiving_messages_cor()
        del A_REDIS_CLIENT  # В доке не нашел описания способа релиза ресурсов. Судя по всему это происходит автоматом
        # во время разрушения объекта.


def redis_get_client():
    return A_REDIS_CLIENT


async def redis_release_lock_no_errors(redis_lock):
    try:
        await redis_lock.release()
    except LockError:  # Исключение будет, если лок уже был освобожден по таймауту
        pass


async def redis_wait_for_message(redis_channel, predicate):
    """Asynchronously wait for message.

    :param predicate: condition to find required message. Signature: def fun(redis_message) -> bool
    :return message: return message when awaited message received.
     Ожидание потенциально бесконечно.
    """
    with redis_get_client().create_subscriber([redis_channel]) as subscriber:

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

    with redis_get_client().create_subscriber([settings.INTERNAL_EVENTS_CHANNEL]) as subscriber:
        try:
            while True:
                # try to receive message
                redis_message = await subscriber.get_msg()
                if redis_message and redis_message["type"] == "message":

                    redis_message_data = redis_message["data"].decode()
                    redis_data_dict = json.loads(redis_message_data)

                    if (
                        redis_data_dict["resource"] == VDI_TASKS_SUBSCRIPTION
                        and redis_data_dict["event"] == WsEventToClient.UPDATED.value  # noqa: W503
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
    pool_id: str, wait_for_result=True, wait_timeout=20, creator=None, deleting_computers_from_ad_enabled=False
):
    """Удаление автоматического пула.

    Если wait_for_result == True, то ждем результат.
    Возврщаем bool успешно или нет прошло удаление.
    """
    from common.models.task import PoolTaskType, TaskStatus  # для избежания цикл ссылки

    # send command to pool worker
    task_id = await request_to_execute_pool_task(pool_id,
                                                 PoolTaskType.POOL_DELETE,
                                                 creator=creator,
                                                 deleting_computers_from_ad_enabled=deleting_computers_from_ad_enabled)

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
    await publish_to_redis(settings.POOL_WORKER_CMD_CHANNEL, json.dumps(cmd_dict))


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
    await publish_to_redis(settings.POOL_WORKER_CMD_CHANNEL, json.dumps(cmd_dict))

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
    await publish_to_redis(settings.POOL_WORKER_CMD_CHANNEL, json.dumps(cmd_dict))


async def send_cmd_to_resume_tasks_associated_with_controller(controller_id):
    """Command to pool worker to resume tasks."""
    cmd_dict = {
        "command": PoolWorkerCmd.RESUME_TASK.name,
        "controller_id": str(controller_id),
    }
    await publish_to_redis(settings.POOL_WORKER_CMD_CHANNEL, json.dumps(cmd_dict))


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
