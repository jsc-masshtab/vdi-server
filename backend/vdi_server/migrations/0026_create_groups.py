
from vdi.db import db

def prepare_insert(dic):
    placeholders = ', '.join(f'${i + 1}' for i, _ in enumerate(dic))
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
        qu = f'insert into role ({keys}) values ({marks})', *values
        await conn.execute(*qu)
        keys, marks, values = prepare_insert(user_role_m2m.admin)
        qu = f'insert into user_role_m2m ({keys}) values ({marks})', *values
        await conn.execute(*qu)
