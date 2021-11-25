# -*- coding: utf-8 -*-
import asyncio
import json


from common.database import db
from common.languages import _local_
from common.log.journal import system_logger
from common.models.active_tk_connection import TkConnectionEvent
from common.models.auth import Entity as EntityModel, EntityOwner as EntityOwnerModel
from common.models.controller import Controller
from common.models.pool import Pool
from common.models.task import PoolTaskType, TaskStatus
from common.models.vm import Vm, VmActionUponUserDisconnect, VmPowerState
from common.settings import (
    INTERNAL_EVENTS_CHANNEL,
    VM_MANGER_DATA_QUERY_INTERVAL,
    WS_MONITOR_CHANNEL_OUT
)
from common.subscription_sources import THIN_CLIENTS_SUBSCRIPTION, WsMessageType
from common.utils import cancel_async_task
from common.veil.veil_gino import EntityType, Status
from common.veil.veil_redis import redis_get_subscriber, request_to_execute_pool_task, wait_for_task_result


class VmManager:
    """Здесь действия над вм, которые выполняются автоматом в ходе выполнения приложения.

    Возможно, логичнее было бы выделить в именной отдельный процесс.
    """

    def __init__(self):
        self._disconnect_action_coroutines = dict()

    async def start(self):

        loop = asyncio.get_event_loop()

        # keeps VMs powered on
        loop.create_task(self._keep_vms_on_task())
        # VM verbose names synchronization
        loop.create_task(self._synchronize_vm_data_task())
        # Действия над ВМ при отключении пользователя
        loop.create_task(self._do_actions_when_user_disconnects_from_vm())

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
                        fields=fields, params={"ids": ids_str}
                    )

                    controller_vms = domains_list_response.paginator_results
                    # print('!!!controller_vms ', controller_vms, flush=True)

                    # Сформировать список вм которые НЕ включены и имеют активный статус
                    vm_ids_to_power_on = [
                        vm_info["id"]
                        for vm_info in controller_vms
                        if vm_info["user_power_state"] != VmPowerState.ON.value  # noqa: W503
                        and vm_info["status"] == Status.ACTIVE.value  # noqa: W503
                    ]
                    # print('!!!vm_ids_to_power_on ', vm_ids_to_power_on, flush=True)
                    if not vm_ids_to_power_on:
                        continue

                    # turn them on
                    await controller.veil_client.domain(template=0).multi_start(
                        entity_ids=vm_ids_to_power_on
                    )

            except asyncio.CancelledError:
                break
            except Exception as ex:
                await system_logger.debug(
                    message=_local_("Keep vms on task error."), description=str(ex)
                )

            await asyncio.sleep(VM_MANGER_DATA_QUERY_INTERVAL)

    async def _synchronize_vm_data_task(self):
        """Если на контроллере меняется имя ВМ, то обновляем его на VDI."""
        with redis_get_subscriber([WS_MONITOR_CHANNEL_OUT]) as subscriber:

            while True:
                try:
                    redis_message = await subscriber.get_msg()

                    if redis_message["type"] == "message":
                        redis_message_data = redis_message["data"].decode()
                        redis_message_data_dict = json.loads(redis_message_data)

                        if (
                            redis_message_data_dict["resource"] == "/domains/"
                            and redis_message_data_dict["msg_type"]  # noqa: W503
                            == WsMessageType.DATA.value  # noqa: W503
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
                    raise
                except Exception as ex:
                    await system_logger.debug(
                        message=_local_("Synchronize vm data task error."),
                        description=str(ex)
                    )

    async def _do_disconnect_action(self, vm_id, user_id):
        """Do vm action."""
        try:
            vm = await Vm.get(vm_id)
            if not vm:
                return
            pool = await Pool.get(vm.pool_id)
            if not pool:
                return

            pool_type = pool.pool_type
            if pool_type == Pool.PoolTypes.RDS:  # Для машины RDS пула действия не предусмотрены
                return
            vm_verbose_name = vm.verbose_name
            action = pool.vm_action_upon_user_disconnect

            # Пока длится таймаут у пользователя есть шанс переподлючиться к машине
            await asyncio.sleep(max(pool.vm_disconnect_action_timeout, 0))  # pool parameter for timeout

            # Открепляем пользователя от ВМ, если опция включена
            if pool.free_vm_from_user and pool_type != Pool.PoolTypes.GUEST:
                if user_id:
                    await vm.remove_users(creator="system", users_list=user_id)

            # Делаем действие в зависимости от типа пула и типа действия при дисконнекте
            if action == VmActionUponUserDisconnect.RECREATE:
                # Проверяем что пул типа guest. RECREATE доступно только для гостевого пула
                if pool_type != Pool.PoolTypes.GUEST:
                    return
                # Открепляем пользователя и устанавливаем статус "Удаляется"
                if user_id:
                    await vm.remove_users(creator="system", users_list=user_id)
                await vm.update(status=Status.DELETING).apply()
                # Создаем таску пересоздания ВМ
                task_id = await request_to_execute_pool_task(vm.id, PoolTaskType.VM_GUEST_RECREATION,
                                                             vm_id=str(vm.id))
                status = await wait_for_task_result(task_id, 180)
                is_action_successful = status and (status == TaskStatus.FINISHED.name)

            elif action == VmActionUponUserDisconnect.SHUTDOWN:
                is_action_successful = await vm.action(action_name="shutdown", force=False)
            elif action == VmActionUponUserDisconnect.SHUTDOWN_FORCED:
                is_action_successful = await vm.action(action_name="shutdown", force=True)
            elif action == VmActionUponUserDisconnect.SUSPEND:
                is_action_successful = await vm.action(action_name="suspend", force=False)
            else:
                return

            # log
            await system_logger.info(message=_local_("Action upon user disconnect completed. "
                                                     "Action: {}. VM: {}. Result: {}.").format(
                action.name, vm_verbose_name, is_action_successful))
        except asyncio.CancelledError:
            return
        except Exception as e:
            await system_logger.warning(message=_local_("Vm post disconnect action error."),
                                        description=str(e))
        finally:
            if vm_id in self._disconnect_action_coroutines:
                del self._disconnect_action_coroutines[vm_id]

    async def _cancel_vm_action_coroutine(self, vm_id):
        """Cancel pending vm actions."""
        if vm_id in self._disconnect_action_coroutines:
            await cancel_async_task(self._disconnect_action_coroutines[vm_id], True)

    async def _do_actions_when_user_disconnects_from_vm(self):
        """Производим действия (через интервал времени) с ВМ после отключения пользователя.

        Считаем, что пользователь закончил работу с ВМ:
        - Когда он отключился от ВМ.
        - Когда пользователь отключился от VDI сервера.
        """
        with redis_get_subscriber([INTERNAL_EVENTS_CHANNEL]) as subscriber:

            while True:
                try:
                    redis_message = await subscriber.get_msg()
                    if redis_message["type"] != "message":
                        continue

                    redis_message_data = redis_message["data"].decode()
                    redis_message_data_dict = json.loads(redis_message_data)

                    if redis_message_data_dict["resource"] != THIN_CLIENTS_SUBSCRIPTION or \
                        redis_message_data_dict["msg_type"] != WsMessageType.DATA.value:  # noqa
                        continue

                    description = redis_message_data_dict.get("description")
                    if description is None:
                        continue

                    vm_id_for_action = None  # id машины над которой произвести действие

                    if description == TkConnectionEvent.VM_CHANGED.name:
                        prev_vm_id = redis_message_data_dict.get("prev_vm_id")
                        vm_id = redis_message_data_dict.get("vm_id")

                        if vm_id is None and prev_vm_id:
                            # Пользователь отключился от ВМ
                            vm_id_for_action = prev_vm_id
                        elif vm_id:
                            # Отменить действие, если пользователь успел подключиться к ВМ до
                            # до таймаута
                            await self._cancel_vm_action_coroutine(vm_id)
                            continue
                    elif description == TkConnectionEvent.CONNECTION_CLOSED.name:
                        # Пользователь отключился от VDI
                        vm_id = redis_message_data_dict.get("vm_id")
                        if vm_id:
                            vm_id_for_action = vm_id

                    if vm_id_for_action:
                        await self._cancel_vm_action_coroutine(vm_id_for_action)
                        # start timed out action here (according to pool settings.)
                        loop = asyncio.get_event_loop()
                        self._disconnect_action_coroutines[vm_id_for_action] = \
                            loop.create_task(self._do_disconnect_action(vm_id_for_action,
                                                                        redis_message.get("user_id")))

                except asyncio.CancelledError:
                    raise
                except Exception as ex:
                    await system_logger.debug(
                        message=_local_("_do_actions_when_user_disconnects_from_vm error."),
                        description=str(ex)
                    )
