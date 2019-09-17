import inspect
from functools import wraps
from typing import List
import re

from vdi.settings import settings
from db.db import db

class Unset:
    pass


def prepare_insert(item: dict):
    placeholders = ', '.join('${}'.format(i + 1) for i, _ in enumerate(item))
    placeholders = '({})'.format(placeholders)
    keys = ', '.join(item.keys())
    keys = '({})'.format(keys)
    values = list(item.values())
    return keys, placeholders, values


def prepare_bulk_insert(items: List[dict]):
    placeholders = []
    values = []
    offset = 0
    for dic in items:
        numbers = ['${}'.format(offset+i+1) for i, _ in enumerate(dic)]
        offset += len(dic)
        numbers = ', '.join(numbers)
        placeholders.append('({})'.format(numbers))
        values.extend(dic.values())
    keys = ', '.join(items[0].keys())
    keys = '({})'.format(keys)
    placeholders = ', '.join(placeholders)
    return keys, placeholders, values


async def insert(table: str, item: dict, returning=None):
    async with db.connect() as conn:
        keys, placeholders, values = prepare_insert(item)
        if returning:
            returning = ' returning {}'.format(returning)
        else:
            returning = ''
        qu = "INSERT INTO {} {} VALUES {}{}".format(table, keys, placeholders, returning), *values
        return await conn.fetch(*qu)


async def bulk_insert(table, items: List[dict], returning: str = None):
    if not items:
        return []
    if returning:
        returning = ' returning {}'.format(returning)
    else:
        returning = ''
    async with db.connect() as conn:
        keys, placeholders, values = prepare_bulk_insert(items)
        qu = "INSERT INTO {} {} VALUES {}{}".format(table, keys, placeholders, returning), *values
        return await conn.fetch(*qu)


def print(msg, _print=print):
    if getattr(settings, 'print', False):
        _print(msg)


def into_words(s):
    return [w for w in s.split() if w]


def clamp_value(my_value, min_value, max_value):
    return max(min(my_value, max_value), min_value)


def validate_name(name_string):
    return re.match('^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$', name_string)

