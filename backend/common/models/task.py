# -*- coding: utf-8 -*-
import uuid

from enum import Enum

from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from common.database import db


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

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    __tablename__ = 'task'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(), unique=False)  # id сущности, с которой связана задача
    status = db.Column(AlchemyEnum(TaskStatus), nullable=False, index=True, default=TaskStatus.INITIAL)
    task_type = db.Column(AlchemyEnum(PoolTaskType), nullable=False, index=True)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Нужно ли возобновлять при старте приложения отмененную таску.
    # Этот флаг нужен, так как есть 2 ситуации, когда таска была отменена:
    # 1) Мы отменили таску намерено во время работы приложения.
    # 2) Таска была отменена при мягком завершении приложения, но тем не менее мы хотим ее продолжения после
    # повторного старта приложения.
    resume_on_app_startup = db.Column(db.Boolean(), nullable=False, default=True)

    priority = db.Column(db.Integer(), nullable=False, default=1)  # Приоритет задачи

    async def set_status(self, status):
        await self.update(status=status).apply()

    #  async def set_resumable(self):
