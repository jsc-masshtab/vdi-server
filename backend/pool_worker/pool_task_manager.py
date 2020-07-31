# -*- coding: utf-8 -*-
import sys

import json

import asyncio

from common.veil.veil_redis import POOL_TASK_QUEUE, a_redis_lpop
from common.languages import lang_init

from pool_worker.pool_tasks import InitPoolTask, ExpandPoolTask, DeletePoolTask

from pool_worker.pool_locks import PoolLocks

from common.models.pool import AutomatedPool
from common.models.tasks import TaskModel, TaskStatus
from sqlalchemy.sql import desc

from common.veil.veil_redis import PoolTaskType

from common.log.journal import system_logger

_ = lang_init()


class PoolTaskManager:
    """Реализует управление задачами"""
    def __init__(self):
        self.pool_locks = PoolLocks()  # todo: можно ли синхронизировать работу над пулом по информации из таблицы task?

        self.task_list = []  # Список, в котором держим объекты выполняемым в данный момент таскок

    async def start(self):
        """Действия при старте менеджера"""

        await system_logger.warning(_('Pool worker: start loop now'))

        # init locks
        await self.pool_locks.fill_start_data()

        # resume tasks
        if '-do-not-resume-tasks' not in sys.argv:
            await self.resume_tasks()

        loop = asyncio.get_event_loop()
        # listening for tasks
        loop.create_task(self.listen_for_work())

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

    async def resume_tasks(self):
        """
        Анализируем таблицу тасок в бд.
        Продолжить таски в статусе IN_PROGRESS и CANCELLED при соблюдении условий:
        - У таски должен быть поднят флаг resume_on_app_startup.
        - Если внезапно присутствуют несколько тасок, работающих над одним пулом, то возобновляем только одну из них
        в следующем приоритете: DELETING > CREATING > EXPANDING.
        """

        await system_logger.warning('Resuming tasks')

        pools = await AutomatedPool.query.gino.all()
        # print('cur auto pools ', pools)
        # Traverse pools and find tasks to launch
        tasks_to_launch = []
        # TODO: имена ВМ перебирает сам VeiL
        for pool in pools:
            # Find a task with the highest priority
            pool_task = await TaskModel.query.where(
                (TaskModel.entity_id == pool.id) &  # noqa
                TaskModel.resume_on_app_startup &  # noqa
                ((TaskModel.status == TaskStatus.IN_PROGRESS) | (TaskModel.status == TaskStatus.CANCELLED))).\
                order_by(desc(TaskModel.priority)).gino.first()

            await system_logger.debug('pool_task {}'.format(pool_task))
            if pool_task:
                # print('pool_task priority', pool_task.priority)
                tasks_to_launch.append(pool_task)

        #  Remove all other tasks (либо как вариант выставить им всем флаг resume_on_app_startup = False)
        task_ids_to_launch = [task.id for task in tasks_to_launch]
        st = await TaskModel.delete.where(TaskModel.id.notin_(task_ids_to_launch)).gino.status()
        await system_logger.debug('Deleted from db tasks: {}'.format(st))

        # # Остальным задачам выставить флаг resume_on_app_startup = False
        # task_ids_to_launch = [task.id for task in tasks_to_launch]
        # st = await TaskModel.update.values(resume_on_app_startup=False).where(
        #     TaskModel.id.notin_(task_ids_to_launch)).gino.status()
        # await system_logger.debug('Other tasks: {}'.format(st))
        # # Возможно стоит ввнести таске столбец дата создания и удалять все таски
        # # кроме последних 100 (Для лога и отладки), чтоб не копить их вечно.

        # Resume tasks
        for task in tasks_to_launch:
            task_data_dict = {'task_id': task.id, 'task_type': task.task_type}
            try:
                await self.launch_task(task_data_dict)
            except Exception as ex:
                await system_logger.error('PoolTaskManager: Cant resume task {} : {}'.format(task, str(ex)))

    async def launch_task(self, task_data_dict):

        # get task data
        task_id = task_data_dict['task_id']
        pool_task_type = task_data_dict['task_type']

        # task execution
        if pool_task_type == PoolTaskType.CREATING.name:
            task = InitPoolTask(self.pool_locks)
            await task.init(task_id, self.task_list)
            task.execute_in_async_task()

        elif pool_task_type == PoolTaskType.EXPANDING.name:
            task = ExpandPoolTask(self.pool_locks)
            await task.init(task_id, self.task_list)
            task.execute_in_async_task()

        elif pool_task_type == PoolTaskType.DELETING.name:
            try:
                full = task_data_dict['deletion_full']
            except KeyError:
                full = True
            task = DeletePoolTask(full, self.pool_locks)
            await task.init(task_id, self.task_list)
            task.execute_in_async_task()
