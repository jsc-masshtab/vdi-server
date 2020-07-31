# -*- coding: utf-8 -*-
from gino_tornado import Gino

from common.settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST

db = Gino()


async def start_gino():
    # TODO: ssl connection
    await db.set_bind(
        'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'.format(DB_USER=DB_USER, DB_PASS=DB_PASS,
                                                                                DB_HOST=DB_HOST, DB_PORT=DB_PORT,
                                                                                DB_NAME=DB_NAME))


async def stop_gino():
    await db.pop_bind().close()
