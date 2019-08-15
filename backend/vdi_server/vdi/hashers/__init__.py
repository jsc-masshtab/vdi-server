
from .hashers import make_password, check_password, get_hasher

from vdi.db import db
from vdi.errors import NotFound

async def check_username(username, raw_password):
    async with db.connect() as conn:
        qu = "select password from public.user where username = $1", username
        users = await conn.fetch(*qu)
    if not users:
        raise NotFound
    [[password]] = users

    async def setter(raw_password):
        encoded = make_password(raw_password)
        async with db.connect() as conn:
            qu = "update public.user set password = $1 where username = $2", encoded, username
            await conn.execute(*qu)

    return await check_password(raw_password, password, setter)
