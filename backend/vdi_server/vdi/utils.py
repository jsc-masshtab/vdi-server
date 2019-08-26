import inspect
from functools import wraps
from typing import List

from vdi.settings import settings
from vdi.db import db

class Unset:
    pass


def prepare_insert(item: dict):
    placeholders = ', '.join(f'${i + 1}' for i, _ in enumerate(item))
    placeholders = f'({placeholders})'
    keys = ', '.join(item.keys())
    keys = f'({keys})'
    values = list(item.values())
    return keys, placeholders, values


def prepare_bulk_insert(items: List[dict]):
    placeholders = []
    values = []
    offset = 0
    for dic in items:
        numbers = [f'${offset+i+1}' for i, _ in enumerate(dic)]
        offset += len(dic)
        numbers = ', '.join(numbers)
        placeholders.append(f'({numbers})')
        values.extend(dic.values())
    keys = ', '.join(items[0].keys())
    keys = f'({keys})'
    placeholders = ', '.join(placeholders)
    return keys, placeholders, values


async def insert(table: str, item: dict, returning=None):
    async with db.connect() as conn:
        keys, placeholders, values = prepare_insert(item)
        if returning:
            returning = f' returning {returning}'
        else:
            returning = ''
        qu = f"INSERT INTO {table} {keys} VALUES {placeholders}{returning}", *values
        return await conn.fetch(*qu)


async def bulk_insert(table, items: List[dict], returning: str = None):
    if not items:
        return []
    if returning:
        returning = f' returning {returning}'
    else:
        returning = ''
    async with db.connect() as conn:
        keys, placeholders, values = prepare_bulk_insert(items)
        qu = f"INSERT INTO {table} {keys} VALUES {placeholders}{returning}", *values
        return await conn.fetch(*qu)


def print(msg, _print=print):
    if getattr(settings, 'print', False):
        _print(msg)


def into_words(s):
    return [w for w in s.split() if w]