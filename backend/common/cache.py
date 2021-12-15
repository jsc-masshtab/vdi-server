# -*- coding: utf-8 -*-
import asyncio

from yaaredis import StrictRedis

from common import settings


REDIS_CLIENT = StrictRedis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT,
    db=settings.REDIS_DB, password=settings.REDIS_PASSWORD,
    max_connections=settings.REDIS_MAX_CLIENT_CONN
)


def clear_cache():
    """Удаляет весь кэш из redis."""
    async def a_clear_cache():
        await REDIS_CLIENT.flushall()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(a_clear_cache())


def get_params_for_cache(*args) -> tuple:
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
