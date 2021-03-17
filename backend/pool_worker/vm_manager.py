# -*- coding: utf-8 -*-
import asyncio
import json

from common.database import db
from common.languages import lang_init
from common.log.journal import system_logger
from common.models.auth import Entity as EntityModel, EntityOwner as EntityOwnerModel
from common.models.controller import Controller
from common.models.pool import Pool
from common.models.vm import Vm, VmPowerState
from common.settings import VM_MANGER_DATA_QUERY_INTERVAL
from common.veil.veil_gino import EntityType, Status
from common.veil.veil_redis import (
    REDIS_CLIENT,
    WS_MONITOR_CHANNEL_OUT,
    a_redis_get_message,
)

_ = lang_init()


class VmManager:
    """Здесь действия над вм, которые выполняются автоматом в ходе выполнения приложения.

    Возможно, логичнее было бы выделить в именной отдельный процесс.
    """

    async def start(self):

        loop = asyncio.get_event_loop()

        # keeps VMs powered on
        loop.create_task(self._keep_vms_on_task())
        # VM verbose names synchronization
        loop.create_task(self._synchronize_vm_data_task())

    async def _keep_vms_on_task(self):
        """Держим ВМ вкл, если ВМ находятся в пуле с флагом keep_vms_on, имеют назначенного юзера и в статусе ACTIVE."""
        while True:
            try:
                controllers = await Controller.get_objects()

                for controller in controllers:

                    # Получить из бд машины имеющие пользователя и которые нужно держать включенными
                    ero_query = EntityOwnerModel.select("entity_id").where(
                        EntityOwnerModel.user_id != None  # noqa: E711
                    )  # noqa

                    entity_query = EntityModel.select("entity_uuid").where(
                        (EntityModel.entity_type == EntityType.VM)
                        & (EntityModel.id.in_(ero_query))  # noqa: W503
                    )

                    local_vm_data = (
                        await db.select([Vm.id])
                        .select_from(Vm.join(Pool))
                        .where(
                            Pool.keep_vms_on
                            & (Pool.controller == controller.id)  # noqa: W503
                            & (Vm.id.in_(entity_query))  # noqa: W503
                        )
                        .gino.all()
                    )
                    vm_ids_from_db = [str(vm_id) for (vm_id,) in local_vm_data]
                    # print('!!!vm_ids_from_db ', vm_ids_from_db, flush=True)
                    if not vm_ids_from_db:
                        continue

                    # Get VMs states from controller
                    ids_str = ",".join(vm_ids_from_db)
                    fields = ["id", "user_power_state", "status"]
                    domains_list_response = await controller.veil_client.domain().list(
                        fields=fields, params={"ids": ids_str})

                    controller_vms = domains_list_response.paginator_results
                    # print('!!!controller_vms ', controller_vms, flush=True)

                    # Сформировать список вм которые НЕ включены и имеют активный статус
                    vm_ids_to_power_on = [vm_info["id"] for vm_info in controller_vms
                                          if vm_info["user_power_state"] != VmPowerState.ON.value and  # noqa: W504
                                          vm_info["status"] == Status.ACTIVE.value]
                    # print('!!!vm_ids_to_power_on ', vm_ids_to_power_on, flush=True)
                    if not vm_ids_to_power_on:
                        continue

                    # turn them on
                    await controller.veil_client.domain(template=0).multi_start(entity_ids=vm_ids_to_power_on)

            except asyncio.CancelledError:
                break
            except Exception as ex:
                await system_logger.debug(message=_("Keep vms on task error."),
                                          description=str(ex))

            await asyncio.sleep(VM_MANGER_DATA_QUERY_INTERVAL)

    async def _synchronize_vm_data_task(self):
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
                await system_logger.debug(message=_("Synchronize vm data task error."),
                                          description=str(ex))
