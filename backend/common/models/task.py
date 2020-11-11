# -*- coding: utf-8 -*-
import uuid
import json
import textwrap

from enum import Enum

from sqlalchemy import Enum as AlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from web_app.front_ws_api.subscription_sources import VDI_TASKS_SUBSCRIPTION

from common.models.auth import Entity

from common.database import db
from common.veil.veil_redis import REDIS_CLIENT, INTERNAL_EVENTS_CHANNEL
from common.veil.veil_gino import AbstractSortableStatusModel, EntityType
from common.languages import lang_init


_ = lang_init()


class PoolTaskType(Enum):

    CREATING_POOL = 'CREATING_POOL'
    EXPANDING_POOL = 'EXPANDING_POOL'
    DELETING_POOL = 'DELETING_POOL'
    DECREASING_POOL = 'DECREASING_POOL'
    VM_PREPARE = 'VM_PREPARE'


class TaskStatus(Enum):

    INITIAL = 'INITIAL'  # Статус в  момент создания таски перед ее запуском
    IN_PROGRESS = 'IN_PROGRESS'  # Задача выполняется.
    FAILED = 'FAILED'  # Было исключение во время выполнения соответствующей корутины.
    CANCELLED = 'CANCELLED'  # Задача отменена.
    FINISHED = 'FINISHED'  # Задача завершилась.


class Task(db.Model, AbstractSortableStatusModel):

    __tablename__ = 'task'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    entity_id = db.Column(UUID(), unique=False)  # id сущности, с которой связана задача
    status = db.Column(AlchemyEnum(TaskStatus), nullable=False, index=True, default=TaskStatus.INITIAL)
    task_type = db.Column(AlchemyEnum(PoolTaskType), nullable=False, index=True)
    created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    started = db.Column(db.DateTime(timezone=True))
    finished = db.Column(db.DateTime(timezone=True))

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

    def form_user_friendly_text(self, entity_name):

        if self.task_type == PoolTaskType.CREATING_POOL:
            return _('Creation of pool {}.').format(entity_name)
        elif self.task_type == PoolTaskType.EXPANDING_POOL:
            return _('Expanding of pool {}.').format(entity_name)
        elif self.task_type == PoolTaskType.DELETING_POOL:
            return _('Deleting of pool {}.').format(entity_name)
        elif self.task_type == PoolTaskType.DECREASING_POOL:
            return _('Decreasing of pool {}.').format(entity_name)
        elif self.task_type == PoolTaskType.VM_PREPARE:
            return _('Preparation of vm {}.').format(entity_name)
        else:
            return ''

    async def set_status(self, status: TaskStatus, message: str = None):

        if status == self.status:
            return

        await self.update(status=status).apply()

        # msg
        if message is None:
            entity_name = await self.get_associated_entity_name()
            message = self.form_user_friendly_text(entity_name)
            # print('!!!message: ', message, flush=True)

        # datetime data
        if status == TaskStatus.IN_PROGRESS:
            # set start time
            await self.update(started=func.now()).apply()

        if status == TaskStatus.FINISHED or status == TaskStatus.FAILED or status == TaskStatus.CANCELLED:
            await self.update(resumable=False).apply()
            # set finish time
            await self.update(finished=func.now()).apply()

            duration = self.finished - self.started
            message += _('  Duration: {}.').format(duration)

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

    async def set_progress(self, progress: int):

        if progress == self.progress:
            return

        await self.update(progress=progress).apply()

        # publish task event
        msg_dict = dict(
            resource=VDI_TASKS_SUBSCRIPTION,
            mgs_type='task_data',
            event='progress_changed',
            message=self.message
        )
        msg_dict.update(self.to_json_serializable_dict())
        REDIS_CLIENT.publish(INTERNAL_EVENTS_CHANNEL, json.dumps(msg_dict))

    async def get_associated_entity_name(self):
        # Запоминаем имя так как его не будет после удаения пула, например.
        if not hasattr(self, '_associated_entity_name'):
            # В зависимости от типа сущности узнаем verbose_name
            # get entity_type
            self._associated_entity_name = ''
            entity = await Entity.query.where(Entity.entity_uuid == self.entity_id).gino.first()
            if entity:
                if entity.entity_type == EntityType.POOL:
                    from common.models.pool import Pool
                    pool = await Pool.get(self.entity_id)
                    self._associated_entity_name = pool.verbose_name if pool else ''

                elif entity.entity_type == EntityType.VM:
                    from common.models.vm import Vm
                    vm = await Vm.get(self.entity_id)
                    self._associated_entity_name = vm.verbose_name if vm else ''

        return self._associated_entity_name

    @staticmethod
    async def set_progress_to_task_associated_with_entity(entity_id, progress):
        """Изменить статус задачи связанной с сущностью entity_id"""

        task_model = await Task.query.where(Task.entity_id == entity_id).gino.first()
        if task_model:
            await task_model.set_progress(progress)

    @staticmethod
    async def get_ids_of_tasks_associated_with_controller(controller_id):

        # pool tasks
        from common.models.pool import Pool
        pool_tasks = await db.select([Task.id]).select_from(Task.join(Pool, Task.entity_id == Pool.id)).where(
            Pool.controller == controller_id).gino.all()
        pool_tasks_ids = [task_to_cancel[0] for task_to_cancel in pool_tasks]

        # vm tasks
        from common.models.vm import Vm
        vm_tasks = await db.select([Task.id]).select_from(
            Task.join(Vm, Task.entity_id == Vm.id).join(Pool, Vm.pool_id == Pool.id)).\
            where(Pool.controller == controller_id).gino.all()
        vm_tasks_ids = [task_to_cancel[0] for task_to_cancel in vm_tasks]

        tasks = [*pool_tasks_ids, *vm_tasks_ids]
        return tasks

    @staticmethod
    async def get_tasks_associated_with_entity(entity_id, task_status):

        tasks = await Task.query.where((Task.entity_id == entity_id) & (Task.status == task_status)).gino.all()
        return tasks
