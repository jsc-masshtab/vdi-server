# -*- coding: utf-8 -*-
import asyncio

import aiohttp

import ujson

from common.languages import _local_
from common.log.journal import system_logger
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from common.models.pool import VmModel
from common.models.settings import Settings
from common.models.vm_connection_data import VmConnectionData
from common.settings import INTERNAL_EVENTS_CHANNEL
from common.subscription_sources import THIN_CLIENTS_SUBSCRIPTION, WsEventToClient
from common.veil.veil_errors import SimpleError
from common.veil.veil_redis import redis_get_client


class GatewayConnection:
    def __init__(self):
        self.tk_connection_listener_is_started = False

    @staticmethod
    async def _get_active_user_ids() -> list:
        """Возвращает список UUID активных пользователей ТК."""
        active_user_ids = await ActiveTkConnection.select("user_id").where(
            ActiveTkConnection.disconnected == None).gino.all()  # noqa

        if active_user_ids:
            active_user_ids = [str(uuid) for uuid in active_user_ids[0]]

        return active_user_ids

    @staticmethod
    async def _get_user_pools(user_id) -> list:
        """Возвращает список пулов присущих пользователю."""
        user = await User.get_object(id_=user_id)
        pools = await user.pools()

        return pools

    @staticmethod
    async def _get_pool_vms(pool_id) -> list:
        """Возвращает список ВМ присущих пулу."""
        vms = (
            await VmModel.query.where(VmModel.pool_id == pool_id)
            .gino.all()
        )
        return vms

    @staticmethod
    async def _get_vm_model(vm_id):
        vm_model = (
            await VmModel.query.where(VmModel.id == vm_id)
            .gino.first()
        )
        return vm_model

    async def _get_controller_address(self, vm_id):
        vm_model = await self._get_vm_model(vm_id)
        controller = await vm_model.controller

        return controller.address

    @staticmethod
    async def _get_veil_domain_info(vm_model):
        veil_domain = await vm_model.vm_client
        await veil_domain.info()

        return veil_domain

    async def _get_vm_address_port(self, veil_domain, connection_type) -> tuple:
        """Возвращает IP-адрес и порт ВМ."""
        if (connection_type == "RDP") or (connection_type == "NATIVE_RDP"):
            vm_address = veil_domain.first_ipv4
            vm_port = 3389
            return vm_address, vm_port

        if connection_type == "SPICE":
            vm_id = veil_domain.id
            vm_address = await self._get_controller_address(vm_id=vm_id)
            vm_port = veil_domain.remote_access_port
            return vm_address, vm_port

        else:
            raise SimpleError(f"{connection_type} connection type is not supported yet.")

    @staticmethod
    async def _save_vm_connection_data(
        vm_id, connection_type, address, port, creator
    ):
        """Создаёт запись в таблице vm_connection_data."""
        vm_connection_data = await VmConnectionData.get_with_params(
            vm_id=vm_id, connection_type=connection_type, active=True
        )
        if vm_connection_data:
            await vm_connection_data.soft_update(
                vm_id=vm_id, connection_type=connection_type,
                address=address, port=port, creator=creator
            )
        else:
            vm_connection_data = await VmConnectionData.soft_create(
                vm_id=vm_id, connection_type=connection_type,
                address=address, port=port, active=True, creator=creator
            )

    @staticmethod
    async def is_port_free(port) -> bool:
        """Проверяет, используется ли порт в таблице vm_connection_data."""
        vm_connection_data = (
            await VmConnectionData.query.where(VmConnectionData.port == port)
            .gino.first()
        )
        if vm_connection_data:
            return False
        else:
            return True

    @staticmethod
    async def get_ports_in_use() -> set:
        """Возвращает все порты из таблицы vm_connection_data."""
        ports_in_use = set()
        row_ports = await VmConnectionData.select("port").gino.all()
        for port in row_ports:
            port = port[0]
            ports_in_use.add(port)

        return ports_in_use

    async def _save_all_vm_connection_data(self, user_id):
        """Сохраняет данные подключения для каждого connection_type всех ВМ пользователя."""
        pools = await self._get_user_pools(user_id=user_id)
        settings = await Settings.get_gateway_settings()
        gateway_address = settings["gateway_address"]

        for pool in pools:
            vms = await self._get_pool_vms(pool_id=pool["id"])
            connection_types = pool["connection_types"]

            for vm in vms:
                for connection_type in connection_types:
                    free_port = await self._get_free_port()
                    await self._save_vm_connection_data(
                        vm_id=vm.id,
                        connection_type=connection_type,
                        address=gateway_address,
                        port=free_port,
                        creator="system"
                    )

    async def _get_free_port(self) -> int:
        """Возвращает свободный порт."""
        settings = await Settings.get_gateway_settings()
        port_range_start = settings["port_range_start"]
        port_range_stop = settings["port_range_stop"]
        ports = {port for port in range(port_range_start, port_range_stop)}
        ports_in_use = await self.get_ports_in_use()
        free_ports = ports - ports_in_use
        free_port = None
        is_free = False

        while not is_free:
            try:
                port = free_ports.pop()
            except KeyError:
                raise SimpleError(_local_("There are no more free ports."))

            is_free = await self.is_port_free(port)

            if is_free:
                free_port = port

        return free_port

    async def _generate_request_body(self) -> list:
        """Формирует тело запроса на открытие соединений."""
        vm_connection_data = (
            await VmConnectionData.query.where(VmConnectionData.active == True)  # noqa
            .gino.all()
        )
        request_data_list = []
        for data in vm_connection_data:
            vm_id = str(data.vm_id)
            vm_model = await self._get_vm_model(vm_id=vm_id)
            veil_domain = await self._get_veil_domain_info(vm_model=vm_model)

            real_vm_address, real_vm_port = await self._get_vm_address_port(
                veil_domain=veil_domain,
                connection_type=data.connection_type.value
            )
            # формируем данные только для включенных ВМ.
            if real_vm_address:
                request_data = dict(
                    real_vm_address=real_vm_address,
                    real_vm_port=real_vm_port,
                    vm_connection_data_address=data.address,
                    vm_connection_data_port=data.port
                )
                request_data_list.append(request_data)

        return request_data_list

    @staticmethod
    async def _connections_request(request_body):
        """Выполняет запрос для запуска соединений на gateway."""
        settings = await Settings.get_gateway_settings()
        gateway_address = settings["gateway_address"]
        gateway_port = settings["gateway_port"]
        url = f"http://{gateway_address}:{gateway_port}/open_connections/"
        await system_logger.debug(_local_("Request to start connections on the gateway."))
        try:
            async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
                await session.post(url=url, json=request_body)
        except Exception as e:
            await system_logger.debug(
                "Error during request to start connections on the gateway:" + str(e)
            )

    @staticmethod
    async def change_settings_request(request_body):
        """Выполняет запрос для изменения настроек на gateway."""
        settings = await Settings.get_gateway_settings()
        gateway_address = settings["gateway_address"]
        gateway_port = settings["gateway_port"]
        # ? Что произойдёт при изменении в БД 'gateway_address' и 'gateway_port'?
        url = f"http://{gateway_address}:{gateway_port}/change_settings/"
        await system_logger.info(_local_("Request to change settings on the gateway."))
        try:
            async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
                await session.post(url=url, json=request_body)
        except Exception as e:
            await system_logger.debug(str(e))

    async def start_connections(self):
        """Запускает соединения на gateway."""
        active_users = await self._get_active_user_ids()

        for user_id in active_users:
            await self._save_all_vm_connection_data(user_id)

        connection_request = await self._generate_request_body()
        await self._connections_request(connection_request)

    async def _do_actions_when_tk_connects(self):
        """Подписывается в Redis на канал INTERNAL_EVENTS_CHANNEL и ловит подключения ТК."""
        with redis_get_client().create_subscriber([INTERNAL_EVENTS_CHANNEL]) as subscriber:
            while True:
                try:
                    redis_message = await subscriber.get_msg()

                    if redis_message["type"] == "message":
                        redis_message_data = redis_message["data"].decode()
                        redis_message_data_dict = ujson.loads(redis_message_data)

                        if redis_message_data_dict.get("resource") == THIN_CLIENTS_SUBSCRIPTION and \
                            redis_message_data_dict.get("event") == WsEventToClient.CREATED.value:  # noqa

                            await system_logger.debug(_local_("Starting gateway connections."))
                            await self.start_connections()

                except Exception as e:
                    await system_logger.debug(
                        "do_actions_when_tk_connects error:" + str(e)
                    )

    async def start_tk_connection_listener(self):
        """Запускает обработчик подключений ТК."""
        if not self.tk_connection_listener_is_started:
            loop = asyncio.get_event_loop()
            loop.create_task(self._do_actions_when_tk_connects())

            self.tk_connection_listener_is_started = True

            await system_logger.info(_local_("TK connection listener is started."))

        else:
            await system_logger.info(_local_("TK connection listener is already running."))
