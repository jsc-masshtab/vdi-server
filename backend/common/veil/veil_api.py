# -*- coding: utf-8 -*-
"""Обобщенный функционал напрямую связанный с VeiL ECP."""
from typing import Optional
import json

from pymemcache.client.base import Client as MemcachedClient

from veil_api_client import (VeilClient, VeilClientSingleton,  # noqa: F401
                             VeilRetryConfiguration, VeilDomainExt, VeilTag,
                             VeilCacheConfiguration, VeilCacheAbstractClient)

from common.settings import VEIL_REQUEST_TIMEOUT, VEIL_MAX_URL_LEN, VEIL_CACHE_TTL, VEIL_CACHE_SERVER  # noqa: F401


class DictSerde:
    """Сериализатор для записи данных ответов в кэш."""

    @staticmethod
    def serialize(key, value):
        """Serialize VeilApiResponse to bytes."""
        if isinstance(value, str):
            return value.encode('utf-8'), 1
        elif isinstance(value, dict):
            return json.dumps(value).encode('utf-8'), 2
        raise Exception('Unknown serialization format')

    @staticmethod
    def deserialize(key, value, flags):
        """Deserialize bytes to dict."""
        if flags == 1:
            return value.decode('utf-8')
        elif flags == 2:
            return json.loads(value.decode('utf-8'))
        raise Exception('Unknown serialization format')


class VdiCacheClient(VeilCacheAbstractClient):
    """Реализация пользовательского кэш-клиента."""

    def __init__(self):
        self.client = MemcachedClient(server=VEIL_CACHE_SERVER, serde=DictSerde())

    async def get_from_cache(self,
                             veil_api_client_request_cor,
                             veil_api_client,
                             method_name,
                             url: str,
                             headers: dict,
                             params: dict,
                             ssl: bool,
                             json_data: Optional[dict] = None,
                             retry_opts: Optional[VeilRetryConfiguration] = None,
                             ttl: int = 0,
                             *args, **kwargs):
        """Метод, который вызовет клиент.

        Внутри себя должен вызывать запись в кэш и чтение из кэша.
        """
        # cache key can`t contain spaces
        # TODO: key must contain params
        cache_key = url.replace(' ', '')
        # Получаем данные из кэша
        cached_result = self.client.get(cache_key)
        # Если данные есть - возвращаем
        if cached_result:
            return cached_result
        # Если в кэше нет актуальных данных - получаем результат запроса
        result_dict = await veil_api_client_request_cor(veil_api_client,
                                                        method_name, url, headers,
                                                        params, ssl, json_data,
                                                        retry_opts, *args, **kwargs)
        # Т.к. ответ преобразуется в VeilApiResponse после вызова этого метода в result_dict будет лежать ответ aiohttp
        if isinstance(result_dict, dict) and result_dict.get('status_code', 0) in (200, 201, 202, 204):
            try:
                # пытаемся сохранить результат в кэш
                await self.save_to_cache(cache_key, result_dict, ttl)
            except Exception as ex_msg:
                print('Failed to save response to cache: {}'.format(ex_msg))
        # Возвращаем ответ aiohttp
        return result_dict

    async def save_to_cache(self, key, data, ttl: int):
        """Сохраняем результат в кэш."""
        return self.client.set(key, data, expire=ttl)


class VdiVeilClient(VeilClient):
    """Отвечает за сетевое взаимодействие с ECP VeiL."""

    async def api_request(self, *args, **kwargs):

        response = await super().api_request(*args, **kwargs)
        if not hasattr(response, 'status_code'):
            raise ValueError('Response is broken. Check veil_api_client version.')

        url = kwargs.get('url')
        params = kwargs.get('params')
        api_object = kwargs.get('api_object')

        if hasattr(api_object, 'api_object_id') and api_object.api_object_id:
            if response.status_code == 404 and isinstance(api_object, VeilDomainExt):
                # TODO: нужно создать событие, что Domain удален на Veil
                from common.models.vm import Vm
                vm_object = await Vm.get(api_object.api_object_id)
                if vm_object and vm_object.active:
                    await vm_object.make_failed()
            elif response.status_code == 404 and isinstance(api_object, VeilTag):
                # TODO: нужно создать событие, что тэг удален на Veil
                from common.models.pool import Pool
                query = Pool.update.values(tag=None).where(Pool.tag == api_object.api_object_id)
                await query.gino.status()

        if response.status_code in {401, 403}:
            # Переключить и деактивировать контроллер
            from common.models.controller import Controller as ControllerModel, Status
            controller_object = await ControllerModel.query.where(
                ControllerModel.address == self.server_address).gino.first()
            if controller_object and isinstance(controller_object, ControllerModel):
                await controller_object.deactivate(status=Status.BAD_AUTH)
            # Остановка клиента происходит при деактивации контроллера

        if not response.success:
            from common.log import system_logger
            error_description = 'url: {}\nparams: {}\nresponse:{}'.format(url, params, response.data)
            await system_logger.warning(message='Veil ECP request error.', description=error_description)

        return response


class VdiVeilClientSingleton(VeilClientSingleton):
    """Хранит ранее инициализированные подключения."""

    __client_instances = dict()

    def __init__(self, retry_opts=None) -> None:
        """Please see help(VeilClientSingleton) for more info."""
        # TODO: включить после решения проблемы с новым ключом кеширования
        # self.__CACHE_OPTS = VeilCacheConfiguration(ttl=VEIL_CACHE_TTL, cache_client=VdiCacheClient())
        self.__TIMEOUT = VEIL_REQUEST_TIMEOUT
        self.__RETRY_OPTS = retry_opts

    def add_client(self, server_address: str, token: str, retry_opts=None) -> 'VeilClient':
        """Пре конфигурированное подключение."""
        if not retry_opts:
            retry_opts = self.__RETRY_OPTS
        if server_address not in self.__client_instances:
            instance = VdiVeilClient(server_address=server_address, token=token,
                                     session_reopen=True, timeout=self.__TIMEOUT, ujson_=True,
                                     retry_opts=retry_opts,
                                     url_max_length=VEIL_MAX_URL_LEN
                                     )
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


retry_configuration = VeilRetryConfiguration(status_codes={401, 403, 400},
                                             timeout=5,
                                             max_timeout=VEIL_REQUEST_TIMEOUT,
                                             timeout_increase_step=1,
                                             num_of_attempts=3)
veil_client = VdiVeilClientSingleton(retry_opts=retry_configuration)


def get_veil_client() -> VeilClientSingleton:
    return veil_client


async def stop_veil_client():
    instances = veil_client.instances
    for instance in instances:
        await instances[instance].close()
