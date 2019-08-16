import inspect
from functools import wraps

from vdi.settings import settings

class Unset:
    pass


def prepare_insert(dic):
    placeholders = ', '.join(f'${i + 1}' for i, _ in enumerate(dic))
    keys = ', '.join(dic.keys())
    values = list(dic.values())
    return keys, placeholders, values


def prepare_bulk_insert(dic):
    raise NotImplementedError
    # placeholders = [f'(${i + 1}, ${i + 2})' for i in range(0, len(dic) * 2, 2)]
    # placeholders = ', '.join(placeholders)
    # params = []
    # for vm_id in vm_ids:
    #     params.extend([vm_id, pool['id']])
    # async with db.connect() as conn:
    #     qu = f'INSERT INTO vm (id, pool_id) VALUES {placeholders}', *params
    #     await conn.fetch(*qu)


def print(msg, _print=print):
    if getattr(settings, 'print', False):
        _print(msg)
