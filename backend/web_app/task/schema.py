# -*- coding: utf-8 -*-
# import asyncio
# import re

import graphene
from graphene import Enum as GrapheneEnum

from sqlalchemy import and_

from common.veil.veil_errors import SimpleError
from common.veil.veil_decorators import administrator_required
from common.veil.veil_redis import (
    send_cmd_to_cancel_tasks,
    send_cmd_to_cancel_tasks_associated_with_controller,
)
from common.veil.veil_gino import EntityType
from common.utils import convert_gino_model_to_graphene_type

from common.models.task import Task, TaskStatus, PoolTaskType

from common.languages import lang_init


_ = lang_init()
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
    message = graphene.String()
    duration = graphene.String()


class TaskQuery(graphene.ObjectType):
    tasks = graphene.List(
        TaskType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        status=TaskStatusGraphene(),
        task_type=TaskTypeGraphene(),
        ordering=graphene.String(),
    )

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
    async def resolve_task(self, _info, id, **kwargs):

        task_model = await Task.get(id)
        if not task_model:
            entity = {"entity_type": EntityType.SYSTEM, "entity_uuid": None}
            raise SimpleError(_("No such task."), entity=entity)

        task_graphene_type = convert_gino_model_to_graphene_type(task_model, TaskType)
        task_graphene_type.duration = task_model.get_task_duration()
        return task_graphene_type

    @staticmethod
    def _calculate_task_duration(task_graphene_type):
        duration = (
            task_graphene_type.finished - task_graphene_type.started
            if (task_graphene_type.finished and task_graphene_type.started)
            else None
        )

        return duration


class CancelTaskMutation(graphene.Mutation):
    """Отменяем задачу"""

    class Arguments:
        task = graphene.UUID()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, task, **kwargs):

        # Check if task exists and has status IN_PROGRESS
        progressing_task_id = await Task.query.where(
            (Task.id == task) & (Task.status == TaskStatus.IN_PROGRESS)
        ).gino.scalar()
        # print("progressing_task_id ", progressing_task_id, flush=True)
        if not progressing_task_id:
            entity = {"entity_type": EntityType.SYSTEM, "entity_uuid": None}
            raise SimpleError(
                _(
                    "No such task or status of task {} is not {}.".format(
                        task, TaskStatus.IN_PROGRESS.name
                    )
                ),
                entity=entity,
            )

        # send cmd
        task_id_str_list = [str(task)]
        send_cmd_to_cancel_tasks(task_id_str_list)
        return CancelTaskMutation(ok=True)


class CancelTaskAssocWithContMutation(graphene.Mutation):
    class Arguments:
        controller = graphene.UUID()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, controller, **kwargs):
        await send_cmd_to_cancel_tasks_associated_with_controller(controller)
        return CancelTaskAssocWithContMutation(ok=True)


class TaskMutations(graphene.ObjectType):
    cancelTask = CancelTaskMutation.Field()
    cancelTaskAssocWith = CancelTaskAssocWithContMutation.Field()


task_schema = graphene.Schema(
    query=TaskQuery, mutation=TaskMutations, auto_camelcase=False
)
