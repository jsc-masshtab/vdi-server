# -*- coding: utf-8 -*-
import asyncio
import re

import graphene
from graphene import Enum as GrapheneEnum

from sqlalchemy import and_

from common.models.task import Task

from common.veil.veil_errors import SimpleError
from common.veil.veil_decorators import administrator_required
from common.veil.veil_redis import send_cmd_to_cancel_tasks
from common.veil.veil_gino import EntityType

from common.models.task import TaskStatus

from common.languages import lang_init
from common.log.journal import system_logger
from common.models.task import PoolTaskType


_ = lang_init()
TaskStatusGraphene = GrapheneEnum.from_enum(TaskStatus)
TaskTypeGraphene = GrapheneEnum.from_enum(PoolTaskType)


def convert_task_model_to_graphene_type(task_model):
    """Create TaskType and fill it with corresponding attributes of task db model"""
    data_dict = dict()
    for task_model_atr_key in task_model.__dict__['__values__']:
        if task_model_atr_key in TaskType.__dict__.keys():
            val = getattr(task_model, task_model_atr_key)
            data_dict[task_model_atr_key] = val

    return TaskType(**data_dict)


class TaskType(graphene.ObjectType):
    id = graphene.UUID()
    entity_id = graphene.UUID()
    status = TaskStatusGraphene()
    task_type = TaskTypeGraphene()
    created = graphene.DateTime()
    priority = graphene.Int()
    progress = graphene.Int(default_value=0)


class TaskQuery(graphene.ObjectType):
    tasks = graphene.List(TaskType, limit=graphene.Int(default_value=100),
                          offset=graphene.Int(default_value=0), status=TaskStatusGraphene(),
                          task_type=TaskTypeGraphene(),ordering=graphene.String())

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
    async def resolve_tasks(self, _info, limit, offset, status=None, task_type=None, ordering=None, **kwargs):

        query = Task.query
        # sorting
        if ordering:
            query = Task.build_ordering(query, ordering)
        # filtering
        filters = TaskQuery.build_filters(status, task_type)
        if filters:
            query = query.where(and_(*filters))
        # request to db
        task_models = await query.limit(limit).offset(offset).gino.all()
        # conversion
        task_graphene_types = [
            convert_task_model_to_graphene_type(task_model)
            for task_model in task_models
        ]
        return task_graphene_types

    @administrator_required
    async def resolve_task(self, _info, id, **kwargs):

        task_model = await Task.get(id)
        if not task_model:
            entity = {'entity_type': EntityType.SYSTEM, 'entity_uuid': None}
            raise SimpleError(_('No such task.'), entity=entity)
        return convert_task_model_to_graphene_type(task_model)


class CancelTaskMutation(graphene.Mutation):
    """Отменяем либо все задачи либо заданые в списке"""
    class Arguments:
        task = graphene.UUID()
        # cancel_all = graphene.Boolean()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, task, **kwargs):

        # Check if task exists and has status IN_PROGRESS
        progressing_task_id = await Task.select('id').where(Task.status == TaskStatus.IN_PROGRESS).gino.scalar()
        print("progressing_task_id ", progressing_task_id, flush=True)
        if progressing_task_id != task:
            entity = {'entity_type': EntityType.SYSTEM, 'entity_uuid': None}
            raise SimpleError(_('No such task or status of task {} is not {} '.format(
                task, TaskStatus.IN_PROGRESS.name)), entity=entity)
        
        # # send cmd
        task_id_str_list = [str(task)]
        send_cmd_to_cancel_tasks(task_id_str_list)
        return CancelTaskMutation(ok=True)


class TaskMutations(graphene.ObjectType):
    cancelTask = CancelTaskMutation.Field()


task_schema = graphene.Schema(query=TaskQuery, mutation=TaskMutations, auto_camelcase=False)
