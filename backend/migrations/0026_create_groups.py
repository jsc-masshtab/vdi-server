import asyncio

from db.db import db

def prepare_insert(dic):
    placeholders = ', '.join('${}'.format(i + 1) for i, _ in enumerate(dic))
    keys = ', '.join(dic.keys())
    values = list(dic.values())
    return keys, placeholders, values

class groups:
    admin = {
        'alias': 'admin'
    }


class user_role_m2m:
    admin = {
        'username': 'admin',
        'role': 'admin',
    }


async def run():
    async with db.connect() as conn:
        keys, marks, values = prepare_insert(groups.admin)
        qu = 'insert into role ({}) values ({})'.format(keys, marks), *values
        await conn.execute(*qu)
    async with db.connect() as conn:
        keys, marks, values = prepare_insert(user_role_m2m.admin)
        qu = 'insert into user_role_m2m ({}) values ({})'.format(keys, marks), *values
        await conn.execute(*qu)


#asyncio.run(run())
loop = asyncio.get_event_loop()
loop.run_until_complete(run())
loop.close()
