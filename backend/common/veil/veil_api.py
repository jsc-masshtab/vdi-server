# -*- coding: utf-8 -*-
"""Обобщенный функционал напрямую связанный с VeiL ECP."""
from veil_api_client import VeilClientSingleton

from common.settings import VEIL_REQUEST_TIMEOUT


veil_client = VeilClientSingleton(timeout=VEIL_REQUEST_TIMEOUT)


def get_veil_client():
    return veil_client


async def stop_veil_client():
    instances = veil_client.instances
    for instance in instances:
        await instances[instance].close()
