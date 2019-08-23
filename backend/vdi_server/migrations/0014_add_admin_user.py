import asyncio

from vdi.db import db
from vdi.hashers import make_password

import itertools
from functools import reduce
import operator as op

from classy_async import wait_all

users = [
    {
        'username': 'admin',
        'password': 'veil',
        'email': 'admin@vdi'
    },
    {
        'username': 'overlord',
        'password': 'guesswho',
        'email': 'overlord@vdi'
    }
]

async def insert(user):
    keys = ', '.join(user)
    user['password'] = make_password(user['password'])
    marks = ', '.join(f'${i+1}' for i, _ in enumerate(user))
    qu = f'insert into public.user ({keys}) values ({marks})', *user.values()
    async with db.connect() as conn:
        await conn.execute(*qu)


async def run():
    tasks = [
        insert(user) for user in users
    ]
    await wait_all(*tasks)


asyncio.run(run())