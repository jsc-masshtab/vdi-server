# -*- coding: utf-8 -*-
"""Обобщенный функционал напрямую связанный с VeiL ECP."""
from veil_api_client import VeilClient, VeilClientSingleton, VeilCacheOptions, VeilRetryOptions
from veil_api_client.api_objects.domain import VeilDomain

from common.settings import VEIL_REQUEST_TIMEOUT, VEIL_CACHE_TTL, VEIL_CACHE_TYPE, VEIL_CACHE_SERVER


class VdiVeilClient(VeilClient):
    """Отвечает за сетевое взаимодействие с ECP VeiL."""

    # TODO: request method instead of get, post, put

    async def get(self, api_object, url, extra_params):
        """Переопределен для перехвата окончательного статуса ответов."""
        response = await super().get(api_object=api_object, url=url, extra_params=extra_params)
        if hasattr(response, 'status_code') and hasattr(api_object, 'api_object_id') and api_object.api_object_id:
            if response.status_code == 404 and isinstance(api_object, VeilDomain):
                from common.models.vm import Vm
                vm_object = await Vm.get(api_object.api_object_id)
                if vm_object and vm_object.active:
                    await vm_object.make_failed()
        if hasattr(response, 'status_code') and response.status_code in {401, 403}:
            # Переключить и деактивировать контроллер
            from common.models.controller import Controller as ControllerModel, Status
            controller_object = await ControllerModel.query.where(
                ControllerModel.address == self.server_address).gino.first()
            if controller_object and isinstance(controller_object, ControllerModel):
                await controller_object.deactivate(status=Status.BAD_AUTH)
            # Остановка клиента происходит при деактивации контроллера
        if not response.success:
            error_description = 'url: {}\nparams: {}\nresponse:{}'.format(url, extra_params, response)
            raise ValueError(error_description)
        return response

    async def post(self, api_object, url: str, json_data: dict = None, extra_params: dict = None):
        """Переопределен для перехвата окончательного статуса ответов."""
        response = await super().post(api_object=api_object, url=url, json_data=json_data, extra_params=extra_params)
        if hasattr(response, 'status_code') and hasattr(api_object, 'api_object_id') and api_object.api_object_id:
            if response.status_code == 404 and isinstance(api_object, VeilDomain):
                from common.models.vm import Vm
                vm_object = await Vm.get(api_object.api_object_id)
                if vm_object and vm_object.active:
                    await vm_object.make_failed()
        if not response.success:
            error_description = 'url: {}\nparams: {}\nbody:{}\nresponse:{}'.format(url, extra_params, json_data,
                                                                                   response)
            raise ValueError(error_description)
        return response

    async def put(self, api_object, url: str, json_data: dict = None, extra_params: dict = None):
        """Переопределен для перехвата окончательного статуса ответов."""
        response = await super().put(api_object=api_object, url=url, json_data=json_data, extra_params=extra_params)
        if hasattr(response, 'status_code') and hasattr(api_object, 'api_object_id') and api_object.api_object_id:
            if response.status_code == 404 and isinstance(api_object, VeilDomain):
                from common.models.vm import Vm
                vm_object = await Vm.get(api_object.api_object_id)
                if vm_object and vm_object.active:
                    await vm_object.make_failed()
        if not response.success:
            error_description = 'url: {}\nparams: {}\nbody:{}\nresponse:{}'.format(url, extra_params, json_data,
                                                                                   response)
            raise ValueError(error_description)
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
                                     # cache_opts=self.__CACHE_OPTS,
                                     retry_opts=self.__RETRY_OPTS)
            self.__client_instances[server_address] = instance
        return self.__client_instances[server_address]

    async def remove_client(self, server_address: str) -> None:
        """Remove and close existing VeilClient instance."""
        if server_address in self.__client_instances:
            _client = self.__client_instances.pop(server_address)
            await _client.close()

    @property
    def instances(self) -> dict:
        """Show all instances of VeilClient."""
        return self.__client_instances


veil_client = VdiVeilClientSingleton(retry_opts=VeilRetryOptions(status_codes={401, 403, 400},
                                                                 timeout=5,
                                                                 max_timeout=VEIL_REQUEST_TIMEOUT,
                                                                 timeout_increase_step=1,
                                                                 num_of_attempts=10))


def get_veil_client() -> 'VeilClientSingleton':
    return veil_client


async def stop_veil_client():
    instances = veil_client.instances
    for instance in instances:
        await instances[instance].close()
