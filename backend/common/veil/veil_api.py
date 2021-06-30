# -*- coding: utf-8 -*-
"""Обобщенный функционал напрямую связанный с VeiL ECP."""
import json
from typing import Optional

from pymemcache.client.base import Client as MemcachedClient

from veil_api_client import (
    VeilCacheAbstractClient,
    VeilClient,
    VeilClientSingleton,  # noqa: F401,
    VeilDomainExt,
    VeilRetryConfiguration,
    VeilTag,
)
from veil_api_client.api_objects import VeilController
from veil_api_client.base import VeilApiResponse

from common.settings import (
    DEBUG,
    VEIL_CACHE_SERVER,
    VEIL_MAX_URL_LEN,
    VEIL_REQUEST_TIMEOUT,
)  # noqa: F401


class DictSerde:
    """Сериализатор для записи данных ответов в кэш."""

    @staticmethod
    def serialize(key, value):
        """Serialize VeilApiResponse to bytes."""
        if isinstance(value, str):
            return value.encode("utf-8"), 1
        elif isinstance(value, dict):
            return json.dumps(value).encode("utf-8"), 2
        raise Exception("Unknown serialization format")

    @staticmethod
    def deserialize(key, value, flags):
        """Deserialize bytes to dict."""
        if flags == 1:
            return value.decode("utf-8")
        elif flags == 2:
            return json.loads(value.decode("utf-8"))
        raise Exception("Unknown serialization format")


class VdiCacheClient(VeilCacheAbstractClient):
    """Реализация пользовательского кэш-клиента."""

    def __init__(self):
        self.client = MemcachedClient(server=VEIL_CACHE_SERVER, serde=DictSerde())

    async def get_from_cache(
        self,
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
        *args,
        **kwargs
    ):
        """Метод, который вызовет клиент.

        Внутри себя должен вызывать запись в кэш и чтение из кэша.
        """
        # cache key can`t contain spaces
        # TODO: key must contain params
        cache_key = url.replace(" ", "")
        # Получаем данные из кэша
        cached_result = self.client.get(cache_key)
        # Если данные есть - возвращаем
        if cached_result:
            return cached_result
        # Если в кэше нет актуальных данных - получаем результат запроса
        result_dict = await veil_api_client_request_cor(
            veil_api_client,
            method_name,
            url,
            headers,
            params,
            ssl,
            json_data,
            retry_opts,
            *args,
            **kwargs
        )
        # Т.к. ответ преобразуется в VeilApiResponse после вызова этого метода в result_dict будет лежать ответ aiohttp
        if isinstance(result_dict, dict) and result_dict.get("status_code", 0) in (
            200,
            201,
            202,
            204,
        ):
            try:
                # пытаемся сохранить результат в кэш
                await self.save_to_cache(cache_key, result_dict, ttl)
            except Exception as ex_msg:
                print("Failed to save response to cache: {}".format(ex_msg))
        # Возвращаем ответ aiohttp
        return result_dict

    async def save_to_cache(self, key, data, ttl: int):
        """Сохраняем результат в кэш."""
        return self.client.set(key, data, expire=ttl)


class VdiVeilClient(VeilClient):
    """Отвечает за сетевое взаимодействие с ECP VeiL."""

    async def api_request(self, *args, **kwargs):
        from common.log import system_logger
        from common.languages import _
        from common.models.controller import Controller as ControllerModel, Status

        url = kwargs.get("url")
        params = kwargs.get("params")
        api_object = kwargs.get("api_object")

        # TODO: remove on 3.0.1
        if DEBUG:
            request_description = "url: {}\nparams: {}".format(url, params)
            await system_logger.info(
                message="veil requests debug", description=request_description
            )

        # Send request to VeiL ECP
        response = await super().api_request(*args, **kwargs)
        if not hasattr(response, "status_code"):
            raise ValueError("Response is broken. Check veil_api_client version.")

        if hasattr(api_object, "api_object_id") and api_object.api_object_id:
            if response.status_code == 404 and isinstance(api_object, VeilDomainExt):
                from common.models.vm import Vm

                vm_object = await Vm.get(api_object.api_object_id)
                if vm_object and vm_object.active:
                    await vm_object.make_failed()
                await system_logger.warning(
                    _("Can`t find VM {} on VeiL ECP.").format(api_object.api_object_id)
                )
            elif response.status_code == 404 and isinstance(api_object, VeilTag):
                from common.models.pool import Pool

                query = Pool.update.values(tag=None).where(
                    Pool.tag == api_object.api_object_id
                )
                await query.gino.status()
                await system_logger.warning(
                    _("Can`t find Tag {} on VeiL ECP.").format(api_object.api_object_id)
                )

        if not response.success:
            # Переключить и деактивировать контроллер
            controller_object = await ControllerModel.query.where(
                ControllerModel.address == self.server_address
            ).gino.first()

            # Остановка клиента происходит при деактивации контроллера
            if controller_object and isinstance(controller_object, ControllerModel):
                if response.status_code in {401, 403}:
                    await controller_object.deactivate(status=Status.BAD_AUTH)
                elif isinstance(api_object, VeilController):
                    # Деактивируем контроллер только для критичных ситуаций
                    await controller_object.deactivate()

            controller_name = (
                controller_object.verbose_name
                if controller_object
                else self.server_address
            )
            error_message = _("VeiL ECP {} request error.").format(controller_name)
            error_description = "status code: {}\nurl: {}\nparams: {}\nresponse:{}".format(
                response.status_code, url, params, response.data
            )
            await system_logger.warning(
                message=error_message, description=error_description
            )

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

    def add_client(
        self, server_address: str, token: str, retry_opts=None
    ) -> "VeilClient":
        """Пре конфигурированное подключение."""
        if not retry_opts:
            retry_opts = self.__RETRY_OPTS
        if server_address not in self.__client_instances:
            instance = VdiVeilClient(
                server_address=server_address,
                token=token,
                session_reopen=True,
                timeout=self.__TIMEOUT,
                ujson_=True,
                retry_opts=retry_opts,
                url_max_length=VEIL_MAX_URL_LEN,
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


retry_configuration = VeilRetryConfiguration(
    status_codes={401, 403},
    timeout=5,
    max_timeout=VEIL_REQUEST_TIMEOUT,
    timeout_increase_step=10,
    num_of_attempts=3,
)
veil_client = VdiVeilClientSingleton(retry_opts=retry_configuration)


def get_veil_client() -> VeilClientSingleton:
    return veil_client


async def stop_veil_client():
    instances = veil_client.instances
    for instance in instances:
        await instances[instance].close()


def compare_error_detail(response: VeilApiResponse, message: str) -> bool:
    """Extract VeiL ECP error detail from response and check message`s occurrence."""
    bad_input_types = not isinstance(response, VeilApiResponse) or not isinstance(
        message, str
    )
    nothing_to_parse = bad_input_types or not response.error_code or not response.errors
    if nothing_to_parse:
        return False
    for error in response.errors:
        error_detail = error.get("detail", "")
        if message in error_detail:
            return True
    return False
