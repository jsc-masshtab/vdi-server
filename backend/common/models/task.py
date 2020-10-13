# -*- coding: utf-8 -*-
import uuid
import json
import textwrap

from enum import Enum

from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


from web_app.front_ws_api.subscription_sources import VDI_TASKS_SUBSCRIPTION

from common.database import db
from common.veil.veil_redis import REDIS_CLIENT, INTERNAL_EVENTS_CHANNEL, redis_error_handle
from common.veil.veil_gino import AbstractSortableStatusModel


class PoolTaskType(Enum):

    CREATING_POOL = 'CREATING_POOL'
    EXPANDING_POOL = 'EXPANDING_POOL'
    DELETING_POOL = 'DELETING_POOL'
    # DECREASING_POOL = 'DECREASING_POOL'


class TaskStatus(Enum):

    INITIAL = 'INITIAL'  # Статус в  момент создания таски перед ее запуском
    IN_PROGRESS = 'IN_PROGRESS'  # Задача выполняется.
    FAILED = 'FAILED'  # Было необработанное исключения во время выполнения соответствующей корутины.
    CANCELLED = 'CANCELLED'  # Задача отменена.
    FINISHED = 'FINISHED'  # Задача завершилась.


class Task(db.Model, AbstractSortableStatusModel):

    __tablename__ = 'task'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(), unique=False)  # id сущности, с которой связана задача
    status = db.Column(AlchemyEnum(TaskStatus), nullable=False, index=True, default=TaskStatus.INITIAL)
    task_type = db.Column(AlchemyEnum(PoolTaskType), nullable=False, index=True)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Нужно ли возобновлять отмененную таску.
    resumable = db.Column(db.Boolean(), nullable=False, default=True)

    priority = db.Column(db.Integer(), nullable=False, default=1)  # Приоритет задачи

    progress = db.Column(db.Integer(), nullable=False, default=0)

    message = db.Column(db.Unicode(length=256), nullable=True)

    def to_json_serializable_dict(self):
        return dict(
            task_id=str(self.id),
            entity_id=str(self.entity_id),
            task_type=self.task_type.name,
            task_status=self.status.name,
            created=str(self.created),
            progress=self.progress,
        )

    @redis_error_handle
    async def set_status(self, status: TaskStatus, message: str = None):

        if status == self.status:
            return

        await self.update(status=status).apply()
        if status == TaskStatus.FINISHED or status == TaskStatus.FAILED:
            await self.update(resumable=False).apply()

        task_id_str = str(self.id)
        if message is None:
            message = 'Status of task {} {} changed to {}'.format(
                self.task_type.name, task_id_str, self.status.name)

        # msg
        shorten_msg = textwrap.shorten(message, width=256)
        await self.update(message=shorten_msg).apply()

        # publish task event
        msg_dict = dict(
            resource=VDI_TASKS_SUBSCRIPTION,
            mgs_type='task_data',
            event='status_changed',
            message=shorten_msg,
        )
        msg_dict.update(self.to_json_serializable_dict())
        REDIS_CLIENT.publish(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))

    @redis_error_handle
    async def set_progress(self, progress: int, message: str = None):

        if progress == self.progress:
            return

        await self.update(progress=progress).apply()

        # publish task event
        task_id_str = str(self.id)
        if message is None:
            message = 'Progress of task {} {} changed to {}'.format(
                self.task_type.name, task_id_str, progress)

        msg_dict = dict(
            resource=VDI_TASKS_SUBSCRIPTION,
            mgs_type='task_data',
            event='progress_changed',
            message=message
        )
        msg_dict.update(self.to_json_serializable_dict())
        REDIS_CLIENT.publish(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))

    @staticmethod
    async def set_progress_to_task_associated_with_entity(entity_id, progress):
        """Изменить статус задачи связанной с сущностью entity_id"""

        task_model = await Task.query.where(Task.entity_id == entity_id).gino.first()
        if task_model:
            await task_model.set_progress(progress)

    @staticmethod
    async def get_ids_of_tasks_associated_with_controller(controller_id):

        from common.models.pool import Pool
        tasks = await db.select([Task.id]).select_from(Task.join(Pool, Task.entity_id == Pool.id)).where(
            Pool.controller == controller_id).gino.all()
        tasks = [task_to_cancel[0] for task_to_cancel in tasks]

        return tasks
