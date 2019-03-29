
from vdi.db import db

from asyncpg.connection import Connection

class Mutation(object):

    @db.connection()
    async def mutate(self, info, conn: Connection):
        return 'done'

import pytest

# @pytest.mark.asyncio
# async def test():
#     await db.init()
#     m = Mutation()
#     r = await m.mutate({':': 'info'}, pool={':': 'pool'})
#     assert r == 'done'


@pytest.mark.asyncio
async def test2():
    await db.init()
    m = Mutation()
    r = await m.mutate({':': 'info'})
    assert r == 'done'