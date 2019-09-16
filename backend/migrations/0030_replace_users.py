import asyncio

from db.db import db
from vdi.hashers import make_password


from classy_async.classy_async import wait_all

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
    marks = ', '.join('${}'.format(i+1) for i, _ in enumerate(user))
    qu = 'insert into public.user ({}) values ({})'.format(keys, marks), *user.values()
    async with db.connect() as conn:
        await conn.execute(*qu)


async def run():
    async with db.connect() as conn:
        await conn.execute('delete from public.user')
    tasks = [
        insert(user) for user in users
    ]
    await wait_all(*tasks)


#asyncio.run(run())
loop = asyncio.get_event_loop()
loop.run_until_complete(run())
loop.close()
