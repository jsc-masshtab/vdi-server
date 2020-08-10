# -*- coding: utf-8 -*-
"""Обобщенный функционал напрямую связанный с VeiL ECP."""
from veil_api_client import VeilClientSingleton, VeilCacheOptions

from common.settings import VEIL_REQUEST_TIMEOUT, VEIL_CACHE_TTL, VEIL_CACHE_TYPE, VEIL_CACHE_SERVER


cache_options = VeilCacheOptions(ttl=VEIL_CACHE_TTL, cache_type=VEIL_CACHE_TYPE, server=VEIL_CACHE_SERVER)
veil_client = VeilClientSingleton(timeout=VEIL_REQUEST_TIMEOUT, cache_opts=cache_options)


def get_veil_client() -> 'VeilClientSingleton':
    return veil_client


async def stop_veil_client():
    instances = veil_client.instances
    for instance in instances:
        await instances[instance].close()
