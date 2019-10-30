import inspect
from functools import wraps
from typing import List
import re
import asyncio

# from vdi.settings import settings


class Unset:
    pass


def get_selections(info, path=''):
    """
    determine what fields are requested in graphql request
    """
    if isinstance(info, Selections):
        return info.get_path(path)

    path = [i for i in path.split('/') if i]

    selections = info.field_asts[0].selection_set.selections

    for item in path:
        for field in selections:
            if field.name.value == item:
                break
        else:
            return
        selections = field.selection_set.selections

    return [
        field.name.value for field in selections
    ]


class Selections(list):

    def _get_item(self, items, key):
        for item in items:
            if isinstance(item, dict) and tuple(item.keys()) == (key,):
                return item[key]
        return ()

    def _is_compound(self, item):
        return isinstance(item, dict) and len(item) == 1

    def get_path(self, path):
        selections = self
        if path:
            path = path.split('/')
            for path_key in path:
                selections = self._get_item(selections, path_key)
        return [
            list(e.keys())[0] if self._is_compound(e) else e
            for e in selections
        ]


def as_list(gen):
    return list(gen())


def make_graphene_type(type, data, fields_map=None):
    """
    create resource object (NodeType, ClusterType...)
    fields_map is used to match Vitalya names with veil names
    """
    dic = {}
    for k, v in data.items():
        if fields_map:
            k = fields_map.get(k, k)
        if k in type._meta.fields:
            dic[k] = v
    obj = type(**dic)
    obj.veil_info = data
    return obj
#
#
# def print(msg, _print=print):
#     if getattr(settings, 'print', False):
#         _print(msg)


def into_words(s):
    return [w for w in s.split() if w]


def clamp_value(my_value, min_value, max_value):
    """
    limit value by min_value and max_value
    """
    return max(min(my_value, max_value), min_value)


def validate_name(name_string):
    """
    validate if name correct
    """
    return re.match('^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$', name_string)


def get_attributes_str(python_object):
    """
    get string of all attributes of an object split by comma
    """
    attributes_str = ', '.join(i for i in dir(python_object) if not i.startswith('__'))
    return attributes_str


async def cancel_async_task(async_task):
    if async_task:
        try:
            async_task.cancel()
            await async_task
        except asyncio.CancelledError:
            pass
