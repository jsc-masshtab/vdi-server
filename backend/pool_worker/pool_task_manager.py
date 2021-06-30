# -*- coding: utf-8 -*-
import asyncio
import json
import sys

from sqlalchemy import and_

from common.database import db
from common.languages import _
from common.log.journal import system_logger
from common.models.pool import Pool
from common.models.task import PoolTaskType, Task, TaskStatus
from common.models.vm import Vm
from common.settings import POOL_TASK_QUEUE, POOL_WORKER_CMD_QUEUE
from common.veil.veil_gino import EntityType
from common.veil.veil_redis import PoolWorkerCmd, a_redis_lpop

from pool_worker.pool_locks import PoolLocks
from pool_worker.pool_tasks import (
    AbstractTask,
    BackupVmsTask,
    DecreasePoolTask,
    DeletePoolTask,
    ExpandPoolTask,
    InitPoolTask,
    PrepareVmTask,
    RecreationGuestVmTask,
    RemoveVmsTask
)


class PoolTaskManager:
    """Реализует управление задачами."""

    def __init__(self):
        self.pool_locks = PoolLocks()  # примитивы для синхронизации задач над пулами. В данный момент
        # применимо только к динамическим (гостевым) пулам

    async def start(self):
        """Действия при старте менеджера."""
        await system_logger.debug("Pool worker: start loop now")

        # init locks
        await self.pool_locks.fill_start_data()

        # resume tasks
        if "-do-not-resume-tasks" not in sys.argv:
            await self.resume_tasks()

        loop = asyncio.get_event_loop()
        # listening for tasks
        loop.create_task(self.listen_for_work())
        # listening for commands
        loop.create_task(self.listen_for_commands())

    async def listen_for_work(self):

        # main loop. Await for work
        while True:
            try:
                # wait for task message
                redis_data = await a_redis_lpop(POOL_TASK_QUEUE)
                await system_logger.debug(
                    "PoolWorker listen_for_work: {}".format(redis_data)
                )
                task_data_dict = json.loads(redis_data.decode())

                await self.launch_task(task_data_dict)

            except asyncio.CancelledError:
                raise
            except Exception as ex:
                await system_logger.error(
                    message=_("Can`t launch task."), description=str(ex)
                )

    async def listen_for_commands(self):
        while True:
            try:
                # wait for message
                redis_data = await a_redis_lpop(POOL_WORKER_CMD_QUEUE)

                # get data from message
                data_dict = json.loads(redis_data.decode())
                command = data_dict["command"]

                await system_logger.debug("listen_for_commands: " + command)

                # cancel_tasks
                if command == PoolWorkerCmd.CANCEL_TASK.name:
                    if "task_ids" in data_dict and "cancel_all" in data_dict:
                        task_ids = data_dict["task_ids"]  # list of id strings
                        cancel_all = data_dict["cancel_all"]
                        await self.cancel_tasks(task_ids, cancel_all)

                    elif "controller_id" in data_dict and "resumable" in data_dict:
                        controller_id = data_dict["controller_id"]
                        resumable = data_dict["resumable"]
                        await self.cancel_tasks_associated_with_controller(
                            controller_id, resumable
                        )

                    elif "entity_id" in data_dict and "resumable" in data_dict:
                        entity_id = data_dict["entity_id"]
                        resumable = data_dict["resumable"]
                        await self.cancel_tasks_associated_with_entity(
                            entity_id, resumable
                        )

                elif command == PoolWorkerCmd.RESUME_TASK.name:
                    try:
                        controller_id = data_dict["controller_id"]
                    except KeyError:
                        controller_id = None
                    await self.resume_tasks(
                        controller_id=controller_id, remove_unresumable_tasks=False
                    )

            except asyncio.CancelledError:
                raise
            except Exception as ex:
                entity = {"entity_type": EntityType.SECURITY, "entity_uuid": None}
                await system_logger.error(
                    "listen_for_commands exception:" + str(ex), entity=entity
                )

    async def resume_tasks(self, controller_id=None, remove_unresumable_tasks=False):
        """Анализируем таблицу тасок в бд.

        Продолжить таски в двух случаях:
        - У таски должен быть поднят флаг resumable и быть статус CANCELLED
        - статус IN_PROGRESS
        remove_unresumable_tasks - удалять ли из бд задачи, которые не могут быть возобновлены.
        """
        await system_logger.debug("Resuming tasks")

        where_conditions = [
            (Task.status == TaskStatus.IN_PROGRESS)
            | (Task.resumable & (Task.status == TaskStatus.CANCELLED))  # noqa: W503
        ]
        if controller_id:
            where_conditions.append(Pool.controller == controller_id)

        # Get tasks to launch (Pools)
        pool_tasks_to_launch = (
            await db.select([Task.id, Task.task_type])
            .select_from(Task.join(Pool, Task.entity_id == Pool.id))
            .where(and_(*where_conditions))
            .gino.all()
        )

        # Get tasks to launch (Vms)
        vm_tasks_to_launch = (
            await db.select([Task.id, Task.task_type])
            .select_from(
                Task.join(Vm, Task.entity_id == Vm.id).join(Pool, Vm.pool_id == Pool.id)
            )
            .where(and_(*where_conditions))
            .gino.all()
        )

        tasks_to_launch = [*pool_tasks_to_launch, *vm_tasks_to_launch]
        # print('!!!tasks_to_launch ', tasks_to_launch, flush=True)

        #  Remove all other tasks
        if remove_unresumable_tasks:
            task_ids_to_launch = [task_id for (task_id, _) in tasks_to_launch]
            st = await Task.delete.where(
                Task.id.notin_(task_ids_to_launch)
            ).gino.status()
            await system_logger.debug("Deleted from db tasks: {}".format(st))

        # Resume tasks
        for task in tasks_to_launch:
            (task_id, task_type) = task
            task_data_dict = {"task_id": task_id, "task_type": task_type.name}
            try:
                await self.launch_task(task_data_dict)
            except Exception as ex:
                await system_logger.error(
                    "PoolTaskManager: Cant resume task {} : {}".format(task, str(ex))
                )

    async def launch_task(self, task_data_dict):
        # print('launch_task ', task_data_dict, flush=True)
        # get task data
        task_id = task_data_dict["task_id"]
        pool_task = task_data_dict["task_type"]

        # task execution
        if pool_task == PoolTaskType.POOL_CREATE.name:
            task = InitPoolTask(self.pool_locks)
            task.execute_in_async_task(task_id)

        elif pool_task == PoolTaskType.POOL_EXPAND.name:
            try:
                ignore_reserve_size = task_data_dict["ignore_reserve_size"]
            except KeyError:
                ignore_reserve_size = False
            task = ExpandPoolTask(
                self.pool_locks, ignore_reserve_size=ignore_reserve_size
            )
            task.execute_in_async_task(task_id)

        elif pool_task == PoolTaskType.POOL_DECREASE.name:
            try:
                new_total_size = task_data_dict["new_total_size"]
            except KeyError:
                return
            task = DecreasePoolTask(self.pool_locks, new_total_size)
            task.execute_in_async_task(task_id)

        elif pool_task == PoolTaskType.POOL_DELETE.name:
            try:
                full = task_data_dict["deletion_full"]
            except KeyError:
                full = True
            task = DeletePoolTask(self.pool_locks, full)
            task.execute_in_async_task(task_id)

        elif pool_task == PoolTaskType.VM_PREPARE.name:
            try:
                full = task_data_dict["full"]
            except KeyError:
                full = True
            task = PrepareVmTask(full)
            task.execute_in_async_task(task_id)

        elif pool_task == PoolTaskType.VMS_BACKUP.name:
            task = BackupVmsTask(entity_type=task_data_dict["entity_type"], creator=task_data_dict["creator"])
            task.execute_in_async_task(task_id)

        elif pool_task == PoolTaskType.VMS_REMOVE.name:
            task = RemoveVmsTask(pool_locks=self.pool_locks, vm_ids=task_data_dict["vm_ids"],
                                 creator=task_data_dict["creator"])
            task.execute_in_async_task(task_id)

        elif pool_task == PoolTaskType.VM_GUEST_RECREATION.name:
            task = RecreationGuestVmTask(
                self.pool_locks,
                vm_id=task_data_dict["vm_id"]
            )
            task.execute_in_async_task(task_id)

    async def cancel_tasks(self, task_ids, cancel_all=False):
        """Cancel_tasks in list or all tasks."""
        # делаем shallow copy так как список AbstractTask.task_list будет уменьшатся в
        #  других корутинах пока мы итерируем
        for task in AbstractTask.get_task_list_shallow_copy():
            if cancel_all or (str(task.task_model.id) in task_ids):
                await task.cancel(wait_for_result=False)

    async def cancel_tasks_associated_with_controller(
        self, controller_id, resumable=False
    ):
        """Сancel_tasks_associated_with_controller."""
        await system_logger.debug("cancel_tasks_associated_with_controller")

        # find tasks
        tasks_to_cancel = await Task.get_ids_of_tasks_associated_with_controller(
            controller_id, TaskStatus.IN_PROGRESS
        )

        # cancel
        for task in AbstractTask.get_task_list_shallow_copy():
            if task.task_model.id in tasks_to_cancel:
                await task.cancel(resumable=resumable, wait_for_result=False)

    async def cancel_tasks_associated_with_entity(self, entity_id, resumable=False):
        """Cancel tasks associated with entity."""
        for task in AbstractTask.get_task_list_shallow_copy():
            if str(task.task_model.entity_id) == entity_id:
                await task.cancel(resumable=resumable, wait_for_result=False)
