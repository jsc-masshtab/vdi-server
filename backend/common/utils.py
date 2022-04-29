import asyncio
import functools
import signal
import uuid
from enum import Enum

from yaaredis import StrictRedis

from common import settings


def clamp_value(my_value, min_value, max_value):
    """Limit value by min_value and max_value."""
    return max(min(my_value, max_value), min_value)


async def cancel_async_task(async_task, wait_for_result=True):
    if async_task:
        try:
            async_task.cancel()
            if wait_for_result:
                await async_task
        except asyncio.CancelledError:
            pass


def extract_ordering_data(ordering):
    reverse = ordering.find("-", 0, 1) == 0
    if reverse:
        ordering = ordering[1:]
    return ordering, reverse


def init_signals(sig_handler):
    """Set exit handler."""
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)


def init_exit_handler():
    async def _shutdown(sig, loop):

        try:
            print("Caught signal {0}".format(sig.name))
            tasks = [
                task
                for task in asyncio.Task.all_tasks()
                if task is not asyncio.tasks.Task.current_task()
            ]
            list(map(lambda task: task.cancel(), tasks))

            results_future = asyncio.gather(*tasks, return_exceptions=True)
            # Был случай, что вернулось не future, поэтому проверяем.
            if asyncio.isfuture(results_future):
                results = await results_future
                print("finished awaiting cancelled tasks, results: {0}".format(results))

        finally:
            loop.stop()

    # init handlers
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(
        signal.SIGTERM,
        functools.partial(asyncio.ensure_future, _shutdown(signal.SIGTERM, loop)),
    )
    loop.add_signal_handler(
        signal.SIGINT,
        functools.partial(asyncio.ensure_future, _shutdown(signal.SIGINT, loop)),
    )


def gino_model_to_json_serializable_dict(model):
    """Gino модель в словарь для json."""
    mode_dict = model.to_dict()
    json_serializable_dict = dict()

    for key, value in mode_dict.items():
        if isinstance(value, Enum):
            json_serializable_dict[key] = value.name
        elif isinstance(value, str):
            if key != "token" and key != "password":
                json_serializable_dict[key] = value
        elif isinstance(value, (int, float)):
            json_serializable_dict[key] = value
        elif value is None:
            json_serializable_dict[key] = None
        else:
            json_serializable_dict[key] = str(value)

    return json_serializable_dict


def convert_gino_model_to_graphene_type(model, graphene_custom_type):
    """Gino модель в graphene тип."""
    data_dict = dict()
    for model_atr_key in model.__dict__["__values__"]:
        if model_atr_key in graphene_custom_type.__dict__.keys():
            val = getattr(model, model_atr_key)
            data_dict[model_atr_key] = val

    return graphene_custom_type(**data_dict)


async def create_subprocess(cmd):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()

    return process.returncode, stdout, stderr


class Cache:
    """Класс реализует методы, обеспечивающие кэширование в Redis."""

    @staticmethod
    async def get_client():
        """Создает клиент Redis."""
        client = StrictRedis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT,
            db=settings.REDIS_DB, password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_MAX_CLIENT_CONN
        )
        return client

    async def get_params(*args) -> tuple:
        """
        Используется для преобразования uuid.UUID в str.

        Преобразование uuid.UUID в str необходимо для возможности их сериализации.
        Сериализованные аргументы используются для генерации уникального ключа кэша.
        """
        cache_params = list()
        for arg in args:
            arg = str(arg)
            cache_params.append(arg)

        return tuple(cache_params)

    @staticmethod
    async def get_expire_time() -> int:
        """Возвращает время хранения кэша."""
        from common.models.settings import Settings
        from common.settings import REDIS_EXPIRE_TIME

        db_settings = await Settings.select("settings").gino.first()
        settings_dict = dict(db_settings[0])
        try:
            expire_time = settings_dict["REDIS_EXPIRE_TIME"]
        except KeyError:
            expire_time = REDIS_EXPIRE_TIME
        return int(expire_time)

    @staticmethod
    async def uuid_to_str(resource_data: dict) -> dict:
        """Принимает словарь и если он содержит значения UUID, то преобразует их в str."""
        for key, value in resource_data.items():
            if isinstance(value, dict):
                await Cache.uuid_to_str(value)
            else:
                if isinstance(value, uuid.UUID):
                    resource_data[key] = str(value)
        return resource_data

    @staticmethod
    async def get_cacheable_resources(resources_list, resource_type_class) -> list:
        resource_class_attrs = dir(resource_type_class)
        cacheable_resources = list()

        for resource_data in resources_list:
            cacheable_resource_data = {key: value for key, value in resource_data.items() if
                                       key in resource_class_attrs}

            cacheable_resource_data = await Cache.uuid_to_str(cacheable_resource_data)
            cacheable_resources.append(cacheable_resource_data)

        return cacheable_resources

    @staticmethod
    async def prepare_cache(cache_key: str, ordering: str = None):
        cache_client = await Cache.get_client()
        expire_time = await Cache.get_expire_time()
        if ordering:
            cache_key += "_" + ordering
        cache = cache_client.cache(cache_key)
        return cache, cache_key, expire_time

    @staticmethod
    async def get_cacheable_resources_list(
        cache,
        cache_key,
        expire_time,
        limit,
        offset,
        resource_type,
        resource_type_class,
        ordering: str = None
    ):
        from web_app.controller.resource_schema import ResourcesQuery

        resources_list = await ResourcesQuery.get_resources_list(
            limit=limit, offset=offset, ordering=ordering, resource_type=resource_type
        )
        cacheable_resources_list = await Cache.get_cacheable_resources(
            resources_list, resource_type_class
        )
        await cache.set(
            key=cache_key, value=cacheable_resources_list, expire_time=expire_time
        )
        return cacheable_resources_list


def str2bool(value):
    return value in ("True", "true", "TRUE", "1")
