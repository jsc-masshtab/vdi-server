
from vdi.db import db

import itertools
from functools import reduce
import operator as op

users = [
    {
        'username': 'admin',
        'password': 'veil',
    },
    {
        'username': 'overlord',
        'password': 'guesswho',
    },
]

def query():
    it = itertools.count(1)
    marks = [f'(${next(it)}, ${next(it)})' for _ in users]
    marks = ', '.join(marks)
    params = [(u['username'], u['password']) for u in users]
    params = reduce(op.add, params)
    return (f"insert into public.user (username, password) values {marks}", *params)


async def run():
    async with db.connect() as conn:
        await conn.fetch(*query())