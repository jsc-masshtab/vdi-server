# -*- coding: utf-8 -*-
"""Обобщенный функционал напрямую связанный с VeiL ECP."""
from veil_api_client import VeilClient, VeilClientSingleton, VeilCacheOptions, VeilDomain

from common.settings import VEIL_REQUEST_TIMEOUT, VEIL_CACHE_TTL, VEIL_CACHE_TYPE, VEIL_CACHE_SERVER
from common.models.vm import Vm


class VdiVeilClient(VeilClient):
    """Отвечает за сетевое взаимодействие с ECP VeiL."""

    async def get(self, api_object, url, extra_params):
        """Переопределен для перехвата окончательного статуса ответов."""
        response = await super().get(api_object=api_object, url=url, extra_params=extra_params)
        if hasattr(response, 'status_code') and hasattr(api_object, 'api_object_id') and api_object.api_object_id:
            if response.status_code == 404 and isinstance(api_object, VeilDomain):
                vm_object = await Vm.get(api_object.api_object_id)
                if vm_object and vm_object.active:
                    await vm_object.make_failed()
        return response


class VdiVeilClientSingleton(VeilClientSingleton):
    """Хранит ранее инициализированные подключения."""

    __client_instances = dict()

    def __init__(self, retry_opts=None) -> None:
        """Please see help(VeilClientSingleton) for more info."""
        self.__TIMEOUT = VEIL_REQUEST_TIMEOUT
        self.__CACHE_OPTS = VeilCacheOptions(ttl=VEIL_CACHE_TTL, cache_type=VEIL_CACHE_TYPE, server=VEIL_CACHE_SERVER)
        self.__RETRY_OPTS = retry_opts

    def add_client(self, server_address: str, token: str, retry_opts=None) -> 'VeilClient':
        """Преконфигурированное подключение."""
        if server_address not in self.__client_instances:
            instance = VdiVeilClient(server_address=server_address, token=token,
                                     session_reopen=True, timeout=self.__TIMEOUT, ujson_=True,
                                     cache_opts=self.__CACHE_OPTS,
                                     retry_opts=self.__RETRY_OPTS)
            self.__client_instances[server_address] = instance
        return self.__client_instances[server_address]

# ---


veil_client = VdiVeilClientSingleton()


def get_veil_client() -> 'VeilClientSingleton':
    return veil_client


async def stop_veil_client():
    instances = veil_client.instances
    for instance in instances:
        await instances[instance].close()
