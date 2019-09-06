import asyncio

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

from vdi.utils import insert

async def run():
    tasks = [
        insert('public.user', user) for user in users
    ]
    await wait_all(*tasks)


asyncio.run(run())