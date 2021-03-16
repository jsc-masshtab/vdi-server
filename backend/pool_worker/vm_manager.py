# -*- coding: utf-8 -*-
import asyncio
import json

from common.database import db
from common.log.journal import system_logger
from common.models.auth import Entity as EntityModel, EntityOwner as EntityOwnerModel
from common.models.controller import Controller
from common.models.pool import Pool
from common.models.vm import Vm
from common.veil.veil_gino import EntityType
from common.veil.veil_redis import (
    REDIS_CLIENT,
    WS_MONITOR_CHANNEL_OUT,
    a_redis_get_message,
)


class VmManager:
    """Здесь действия над вм, которые выполняются автоматом в ходе выполнения приложения.

    Возможно, логичнее было бы выделить в именной отдельный процесс.
    """

    def __init__(self):
        self.query_interval = 30

    async def start(self):

        loop = asyncio.get_event_loop()

        # keeps VMs powered on
        loop.create_task(self._keep_vms_on_task())
        # VM verbose names synchronization
        loop.create_task(self._synchronize_vm_names_task())

    async def _keep_vms_on_task(self):
        """Держим ВМ вкюченными, если ВМ находятся в пуле с поднятым флагом keep_vms_on и имеют назначенного юзера."""
        while True:

            # get vm info from controllers
            controllers = await Controller.get_objects()

            for controller in controllers:

                # get vms which have users and should be kept on
                ero_query = EntityOwnerModel.select("entity_id").where(
                    EntityOwnerModel.user_id != None  # noqa: E711
                )  # noqa

                entity_query = EntityModel.select("entity_uuid").where(
                    (EntityModel.entity_type == EntityType.VM)
                    & (EntityModel.id.in_(ero_query))  # noqa: W503
                )

                local_vm_data_list = (
                    await db.select([Vm.id])
                    .select_from(Vm.join(Pool))
                    .where(
                        Pool.keep_vms_on
                        & (Pool.controller == controller.id)  # noqa: W503
                        & (Vm.id.in_(entity_query))  # noqa: W503
                    )
                    .gino.all()
                )
                vm_ids_list = [str(vm_id) for (vm_id,) in local_vm_data_list]
                # print('!!!vm_ids_list ', vm_ids_list, flush=True)

                # turn them on
                if len(vm_ids_list) > 0:
                    await controller.veil_client.domain(template=0).multi_start(
                        entity_ids=vm_ids_list
                    )

            await asyncio.sleep(self.query_interval)

    async def _synchronize_vm_names_task(self):
        """Если на контроллере меняется имя ВМ, то обновляем его на VDI."""
        redis_subscriber = REDIS_CLIENT.pubsub()
        redis_subscriber.subscribe(WS_MONITOR_CHANNEL_OUT)

        while True:
            try:
                redis_message = await a_redis_get_message(redis_subscriber)

                if redis_message["type"] == "message":
                    redis_message_data = redis_message["data"].decode()
                    redis_message_data_dict = json.loads(redis_message_data)

                    if (
                        redis_message_data_dict["resource"] == "/domains/"
                        and redis_message_data_dict["msg_type"] == "data"  # noqa: W503
                    ):
                        vm_id = redis_message_data_dict["id"]
                        vm = await Vm.get(vm_id)

                        # Если ВМ найдена и имя изменилось, то делаем апдэйт
                        if vm:
                            fresh_name = redis_message_data_dict["object"][
                                "verbose_name"
                            ]
                            if vm.verbose_name != fresh_name:
                                # await vm.soft_update(verbose_name=fresh_name, creator='system')
                                await vm.update(verbose_name=fresh_name).apply()

            except asyncio.CancelledError:
                break
            except Exception as ex:
                await system_logger.debug(str(ex))
