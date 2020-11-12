# -*- coding: utf-8 -*-
import sys

import json

import asyncio

from pool_worker.pool_tasks import InitPoolTask, ExpandPoolTask, DecreasePoolTask, DeletePoolTask, PrepareVmTask
from pool_worker.pool_locks import PoolLocks

from common.veil.veil_redis import POOL_TASK_QUEUE, POOL_WORKER_CMD_QUEUE, PoolWorkerCmd, a_redis_lpop
from common.veil.veil_gino import EntityType

from common.languages import lang_init

from common.models.vm import Vm
from common.models.pool import Pool
from common.models.task import Task, TaskStatus, PoolTaskType
from common.database import db

from sqlalchemy import and_

from common.log.journal import system_logger


_ = lang_init()


class PoolTaskManager:

    """Реализует управление задачами"""
    def __init__(self):
        self.pool_locks = PoolLocks()

        self.task_list = []  # Список, в котором держим объекты выполняемым в данный момент таскок

    async def start(self):
        """Действия при старте менеджера"""

        await system_logger.debug('Pool worker: start loop now')

        # init locks
        await self.pool_locks.fill_start_data()

        # resume tasks
        if '-do-not-resume-tasks' not in sys.argv:
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
                await system_logger.debug('PoolWorker listen_for_work: {}'.format(redis_data))
                task_data_dict = json.loads(redis_data.decode())

                await self.launch_task(task_data_dict)

            except asyncio.CancelledError:
                raise
            except Exception as ex:
                await system_logger.error('exception:' + str(ex))

    async def listen_for_commands(self):
        while True:
            try:
                # wait for message
                redis_data = await a_redis_lpop(POOL_WORKER_CMD_QUEUE)

                # get data from message
                data_dict = json.loads(redis_data.decode())
                command = data_dict['command']

                await system_logger.debug('listen_for_commands: ' + command)

                # cancel_tasks
                if command == PoolWorkerCmd.CANCEL_TASK.name:
                    if 'task_ids' in data_dict and 'cancel_all' in data_dict:
                        task_ids = data_dict['task_ids']  # list of id strings
                        cancel_all = data_dict['cancel_all']
                        await self.cancel_tasks(task_ids, cancel_all)

                    elif 'controller_id' in data_dict:
                        controller_id = data_dict['controller_id']
                        resumable = data_dict['resumable']
                        await self.cancel_tasks_associated_with_controller(controller_id, resumable)

                elif command == PoolWorkerCmd.RESUME_TASK.name:
                    try:
                        controller_id = data_dict['controller_id']
                        await self.resume_tasks(controller_id=controller_id, remove_unresumable_tasks=False)
                    except KeyError:
                        await system_logger.error('Cant resume tasks')

            except asyncio.CancelledError:
                raise
            except Exception as ex:
                entity = {'entity_type': EntityType.SECURITY, 'entity_uuid': None}
                await system_logger.error('listen_for_commands exception:' + str(ex), entity=entity)

    async def resume_tasks(self, controller_id=None, remove_unresumable_tasks=False):
        """
        Анализируем таблицу тасок в бд.
        Продолжить таски  в двух случаях:
        - У таски должен быть поднят флаг resumable и быть статус CANCELLED
        - статус IN_PROGRESS
        remove_unresumable_tasks - удалять ли из бд задачи, которые не могут быть возобновлены.
        """
        await system_logger.debug('Resuming tasks')

        where_conditions = \
            [(Task.status == TaskStatus.IN_PROGRESS) | (Task.resumable & (Task.status == TaskStatus.CANCELLED))]
        if controller_id:
            where_conditions.append(Pool.controller == controller_id)

        # Get tasks to launch (Pools)
        pool_tasks_to_launch = await db.select([Task.id, Task.task_type]).select_from(
            Task.join(Pool, Task.entity_id == Pool.id)).where(and_(*where_conditions)).gino.all()

        # Get tasks to launch (Vms)
        vm_tasks_to_launch = await db.select([Task.id, Task.task_type]).select_from(
            Task.join(Vm, Task.entity_id == Vm.id).join(Pool, Vm.pool_id == Pool.id)).\
            where(and_(*where_conditions)).gino.all()

        tasks_to_launch = [*pool_tasks_to_launch, *vm_tasks_to_launch]
        # print('!!!tasks_to_launch ', tasks_to_launch, flush=True)

        #  Remove all other tasks
        if remove_unresumable_tasks:
            task_ids_to_launch = [task_id for (task_id, _) in tasks_to_launch]
            st = await Task.delete.where(Task.id.notin_(task_ids_to_launch)).gino.status()
            await system_logger.debug('Deleted from db tasks: {}'.format(st))

        # Resume tasks
        for task in tasks_to_launch:
            (task_id, task_type) = task
            task_data_dict = {'task_id': task_id, 'task_type': task_type.name}
            try:
                await self.launch_task(task_data_dict)
            except Exception as ex:
                await system_logger.error('PoolTaskManager: Cant resume task {} : {}'.format(task, str(ex)))

    async def launch_task(self, task_data_dict):
        # print('launch_task ', task_data_dict, flush=True)
        # get task data
        task_id = task_data_dict['task_id']
        pool_task_type = task_data_dict['task_type']

        # task execution
        if pool_task_type == PoolTaskType.POOL_CREATE.name:
            task = InitPoolTask(self.pool_locks)
            await task.init(task_id, self.task_list)
            task.execute_in_async_task()

        elif pool_task_type == PoolTaskType.POOL_EXPAND.name:
            try:
                ignore_reserve_size = task_data_dict['ignore_reserve_size']
                wait_for_lock = task_data_dict['wait_for_lock']
            except KeyError:
                ignore_reserve_size = False
                wait_for_lock = False
            task = ExpandPoolTask(self.pool_locks, ignore_reserve_size=ignore_reserve_size, wait_for_lock=wait_for_lock)
            await task.init(task_id, self.task_list)
            task.execute_in_async_task()

        elif pool_task_type == PoolTaskType.POOL_DECREASE.name:
            try:
                new_total_size = task_data_dict['new_total_size']
            except KeyError:
                return
            task = DecreasePoolTask(self.pool_locks, new_total_size)
            await task.init(task_id, self.task_list)
            task.execute_in_async_task()

        elif pool_task_type == PoolTaskType.POOL_DELETE.name:
            try:
                full = task_data_dict['deletion_full']
            except KeyError:
                full = True
            task = DeletePoolTask(self.pool_locks, full)
            await task.init(task_id, self.task_list)
            task.execute_in_async_task()

        elif pool_task_type == PoolTaskType.VM_PREPARE.name:
            task = PrepareVmTask()
            await task.init(task_id, self.task_list)
            task.execute_in_async_task()

    async def cancel_tasks(self, task_ids, cancel_all=False):
        """cancel_tasks in list or all tasks"""

        task_list = list(self.task_list)  # делаем shallow copy так как список self.task_list будет уменьшатся в
        #  других корутинах пока мы итерируем

        for task in task_list:
            if cancel_all or (str(task.task_model.id) in task_ids):
                await task.cancel(wait_for_result=False)

    async def cancel_tasks_associated_with_controller(self, controller_id, resumable=False):
        """cancel_tasks_associated_with_controller"""
        await system_logger.debug('cancel_tasks_associated_with_controller')

        # find tasks
        tasks_to_cancel = await Task.get_ids_of_tasks_associated_with_controller(controller_id, TaskStatus.IN_PROGRESS)
        # print('!!!tasks_to_cancel', tasks_to_cancel, flush=True)
        # cancel
        task_list = list(self.task_list)  # shallow copy
        for task in task_list:
            if task.task_model.id in tasks_to_cancel:
                await task.cancel(resumable=resumable, wait_for_result=False)
