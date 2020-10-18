# -*- coding: utf-8 -*-
from gino_tornado import Gino

from common.settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST

db = Gino()
bind_str = 'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'.format(DB_USER=DB_USER, DB_PASS=DB_PASS,
                                                                                   DB_HOST=DB_HOST, DB_PORT=DB_PORT,
                                                                                   DB_NAME=DB_NAME)


async def start_gino(app=None):
    # TODO: ssl connection
    if app:
        return await db.init_app(app, dsn=bind_str)
    return await db.set_bind(bind_str)


async def stop_gino():
    pop_bind = db.pop_bind()
    await pop_bind.close()
