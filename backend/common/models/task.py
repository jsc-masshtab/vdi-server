# -*- coding: utf-8 -*-
import textwrap
import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Enum as AlchemyEnum, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from common.database import db
from common.subscription_sources import VDI_TASKS_SUBSCRIPTION
from common.veil.veil_gino import AbstractSortableStatusModel
from common.veil.veil_redis import publish_data_in_internal_channel


class PoolTaskType(Enum):

    POOL_CREATE = "POOL_CREATE"
    POOL_EXPAND = "POOL_EXPAND"
    POOL_DELETE = "POOL_DELETE"
    POOL_DECREASE = "POOL_DECREASE"
    VM_PREPARE = "VM_PREPARE"
    VMS_BACKUP = "VMS_BACKUP"
    VMS_REMOVE = "VMS_REMOVE"
    VM_GUEST_RECREATION = "VM_GUEST_RECREATION"


class TaskStatus(Enum):

    INITIAL = "INITIAL"  # Статус в  момент создания таски перед ее запуском
    IN_PROGRESS = "IN_PROGRESS"  # Задача выполняется.
    FAILED = "FAILED"  # Было исключение во время выполнения соответствующей корутины.
    CANCELLED = "CANCELLED"  # Задача отменена.
    FINISHED = "FINISHED"  # Задача завершилась.


class Task(db.Model, AbstractSortableStatusModel):

    __tablename__ = "task"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(), unique=False)  # id сущности, с которой связана задача
    status = db.Column(
        AlchemyEnum(TaskStatus), nullable=False, index=True, default=TaskStatus.INITIAL
    )
    task_type = db.Column(db.Unicode(length=256), nullable=False, index=True)  # тип строка а не enum
    # для облегчения добавлния новых типов задач, чтобы не создавать каждый раз миграцию
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    started = db.Column(db.DateTime(timezone=True))
    finished = db.Column(db.DateTime(timezone=True))

    # Нужно ли возобновлять отмененную таску.
    resumable = db.Column(db.Boolean(), nullable=False, default=True)

    priority = db.Column(db.Integer(), nullable=False, default=1)  # Приоритет задачи

    progress = db.Column(db.Integer(), nullable=False, default=0)

    message = db.Column(db.Unicode(length=256), nullable=True)

    def get_task_duration(self):
        if self.started:
            if self.finished:
                duration = self.finished - self.started
            else:
                duration = datetime.now(timezone.utc) - self.started
        else:
            duration = "00000000"

        return str(duration)[:-7]

    async def set_status(self, status: TaskStatus, message: str = None):

        if status == self.status:
            return

        await self.update(status=status).apply()

        # msg
        if message:
            shorten_msg = textwrap.shorten(message, width=256)
            await self.update(message=shorten_msg).apply()

        # datetime data
        if status == TaskStatus.IN_PROGRESS:
            # set start time
            await self.update(started=func.now()).apply()
        elif (
            status == TaskStatus.FINISHED
            or status == TaskStatus.FAILED  # noqa: W503
            or status == TaskStatus.CANCELLED  # noqa: W503
        ):
            # set finish time
            await self.update(finished=func.now()).apply()

            await self.set_progress(100)

        # возобновляемое
        if status == TaskStatus.FINISHED or status == TaskStatus.FAILED:
            await self.update(resumable=False).apply()

        # publish task event
        await publish_data_in_internal_channel(VDI_TASKS_SUBSCRIPTION, "UPDATED", self)

    async def set_progress(self, progress: int):

        if progress == self.progress:
            return

        await self.update(progress=progress).apply()

        # publish task event
        await publish_data_in_internal_channel(VDI_TASKS_SUBSCRIPTION, "UPDATED", self)

    @classmethod
    async def soft_create(cls, entity_id, task_type, **kwargs):
        task = await Task.create(entity_id=entity_id, task_type=task_type)

        await publish_data_in_internal_channel(VDI_TASKS_SUBSCRIPTION, "CREATED", task)

        return task

    @staticmethod
    async def set_progress_to_task_associated_with_entity(entity_id, progress):
        """Изменить статус задачи связанной с сущностью entity_id."""
        task_model = await Task.query.where(Task.entity_id == entity_id).gino.first()
        if task_model:
            await task_model.set_progress(progress)

    @staticmethod
    async def get_ids_of_tasks_associated_with_controller(controller_id, task_status):

        from common.models.pool import Pool

        where_conditions = [
            Pool.controller == controller_id,
            Task.status == task_status,
        ]

        # pool tasks
        pool_tasks = (
            await db.select([Task.id])
            .select_from(Task.join(Pool, Task.entity_id == Pool.id))
            .where(and_(*where_conditions))
            .gino.all()
        )
        pool_tasks_ids = [task_to_cancel[0] for task_to_cancel in pool_tasks]

        # vm tasks
        from common.models.vm import Vm

        vm_tasks = (
            await db.select([Task.id])
            .select_from(
                Task.join(Vm, Task.entity_id == Vm.id).join(Pool, Vm.pool_id == Pool.id)
            )
            .where(and_(*where_conditions))
            .gino.all()
        )
        vm_tasks_ids = [task_to_cancel[0] for task_to_cancel in vm_tasks]

        tasks = [*pool_tasks_ids, *vm_tasks_ids]
        return tasks

    @staticmethod
    async def get_tasks_associated_with_entity(entity_id, task_status=None,
                                               task_type=None):

        where_conditions = [Task.entity_id == entity_id]
        if task_status:
            where_conditions.append(Task.status == task_status)
        if task_type:
            where_conditions.append(Task.task_type == task_type.name)

        tasks = await Task.query.where(and_(*where_conditions)).gino.all()
        return tasks
