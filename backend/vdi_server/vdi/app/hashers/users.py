from . import check_password, make_password

from vdi.db import db

def check_username(username, raw_password):
    encoded = make_password(raw_password)

    async def setter(raw_password):
        async with db.connect() as conn:
            qu = "update table public.user set password = $1 where username = $2", encoded, username
            await conn.execute(*qu)

    return check_password(raw_password, encoded, setter)