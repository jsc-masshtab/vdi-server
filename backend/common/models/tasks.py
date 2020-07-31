# -*- coding: utf-8 -*-
# todo: Этот файл определенно будет помещен в папку общих модулей, так как он используется
# как минимум в двух процессах: main_app и pool_worker
import uuid
# import asyncio

from enum import Enum
from sqlalchemy import Enum as AlchemyEnum

from sqlalchemy.dialects.postgresql import UUID

from common.database import db


class TaskStatus(Enum):

    INITIAL = 'INITIAL'  # Статус в  момент создания таски перед ее запуском
    IN_PROGRESS = 'IN_PROGRESS'  # Задача выполняется.
    FAILED = 'FAILED'  # Было необработанное исключения во время выполнения соответствующей корутины.
    CANCELLED = 'CANCELLED'  # Задача отменена.
    FINISHED = 'FINISHED'  # Задача завершилась.


class TaskModel(db.Model):
    # TODO: @solomin мы же не используем такой префикс в наименовании моделей
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)

    __tablename__ = 'task'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(), unique=False)  # id сущности, с которой связана задача
    status = db.Column(AlchemyEnum(TaskStatus), nullable=False, index=True, default=TaskStatus.INITIAL)
    task_type = db.Column(db.Unicode(length=128), nullable=False, unique=False, default='Unknown')  # maybe enum

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
