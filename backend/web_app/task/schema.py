# -*- coding: utf-8 -*-
# import asyncio
# import re

import graphene
from graphene import Enum as GrapheneEnum

from sqlalchemy import and_

from common.database import db
from common.graphene_utils import ShortString
from common.languages import _local_
from common.log.journal import system_logger
from common.models.controller import Controller
from common.models.task import PoolTaskType, Task, TaskStatus
from common.utils import convert_gino_model_to_graphene_type
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SimpleError
from common.veil.veil_gino import EntityType
from common.veil.veil_redis import (
    send_cmd_to_cancel_tasks,
    send_cmd_to_cancel_tasks_associated_with_controller,
)

TaskStatusGraphene = GrapheneEnum.from_enum(TaskStatus)
TaskTypeGraphene = GrapheneEnum.from_enum(PoolTaskType)


class TaskType(graphene.ObjectType):
    id = graphene.UUID()
    entity_id = graphene.UUID()
    status = TaskStatusGraphene()
    task_type = TaskTypeGraphene()
    created = graphene.DateTime()
    started = graphene.DateTime()
    finished = graphene.DateTime()
    priority = graphene.Int()
    progress = graphene.Int(default_value=0)
    message = graphene.Field(ShortString)
    duration = graphene.Field(ShortString)
    creator = graphene.Field(ShortString)


class TaskQuery(graphene.ObjectType):
    tasks = graphene.List(
        TaskType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        status=TaskStatusGraphene(),
        task_type=TaskTypeGraphene(),
        ordering=ShortString(),
    )
    tasks_count = graphene.Int(default_value=100, status=TaskStatusGraphene(), task_type=TaskTypeGraphene())

    task = graphene.Field(TaskType, id=graphene.UUID())

    @staticmethod
    def build_filters(status, task_type):
        filters = []
        if status:
            filters.append((Task.status == status))
        if task_type:
            filters.append((Task.task_type == task_type))

        return filters

    @administrator_required
    async def resolve_tasks(
        self,
        _info,
        limit,
        offset,
        status=None,
        task_type=None,
        ordering="-created",
        **kwargs
    ):

        query = Task.query

        query = Task.build_ordering(query, ordering)

        # filtering
        filters = TaskQuery.build_filters(status, task_type)
        if filters:
            query = query.where(and_(*filters))
        # request to db
        task_models = await query.limit(limit).offset(offset).gino.all()
        # conversion
        task_graphene_types = []
        for task_model in task_models:
            task_graphene_type = convert_gino_model_to_graphene_type(
                task_model, TaskType
            )
            task_graphene_type.duration = task_model.get_task_duration()
            task_graphene_types.append(task_graphene_type)

        return task_graphene_types

    @administrator_required
    async def resolve_tasks_count(self, _info, status=None, task_type=None, **kwargs):
        query = Task.query
        filters = TaskQuery.build_filters(status, task_type)
        if filters:
            query = query.where(and_(*filters))

        return await db.select([db.func.count()]).select_from(query.alias()).gino.scalar()

    @administrator_required
    async def resolve_task(self, _info, id, **kwargs):

        task_model = await Task.get(id)
        if not task_model:
            entity = {"entity_type": EntityType.SYSTEM, "entity_uuid": None}
            raise SimpleError(_local_("No such task."), entity=entity)

        task_graphene_type = convert_gino_model_to_graphene_type(task_model, TaskType)
        task_graphene_type.duration = task_model.get_task_duration()
        return task_graphene_type


class CancelTaskMutation(graphene.Mutation):
    """Отменяем задачу."""

    class Arguments:
        task = graphene.UUID()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, task, creator, **kwargs):

        # Check if task exists and has status IN_PROGRESS
        task_model = await Task.query.where((Task.id == task) & (Task.status == TaskStatus.IN_PROGRESS)).gino.first()

        if not task_model:
            entity = {"entity_type": EntityType.SYSTEM, "entity_uuid": None}
            raise SimpleError(
                _local_(
                    "No such task or status of task {} is not {}.".format(
                        task, TaskStatus.IN_PROGRESS.name
                    )
                ),
                entity=entity,
            )

        # send cmd
        task_id_str_list = [str(task)]
        await send_cmd_to_cancel_tasks(task_id_str_list)

        # log
        await system_logger.info(_local_("Task '{} ({})' is requested to be cancelled by user {}.").format(
            task_model.message, task_model.task_type, creator), user=creator)

        return CancelTaskMutation(ok=True)


class CancelTaskAssocWithContMutation(graphene.Mutation):
    class Arguments:
        controller = graphene.UUID()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, controller, creator, **kwargs):

        controller_model = await Controller.get(controller)

        if not controller_model:
            entity = {"entity_type": EntityType.SYSTEM, "entity_uuid": None}
            raise SimpleError(
                _local_("No controller with id {}.".format(controller)),
                entity=entity,
            )

        # send cmd
        await send_cmd_to_cancel_tasks_associated_with_controller(controller)

        # log
        await system_logger.info(_local_("Tasks associated with controller {} are requested "
                                         "to be cancelled by user {}.").format(
            controller_model.verbose_name, creator), user=creator)

        return CancelTaskAssocWithContMutation(ok=True)


class TaskMutations(graphene.ObjectType):
    cancelTask = CancelTaskMutation.Field()
    cancelTaskAssocWith = CancelTaskAssocWithContMutation.Field()


task_schema = graphene.Schema(
    query=TaskQuery, mutation=TaskMutations, auto_camelcase=False
)
