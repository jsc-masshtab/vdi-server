

import asyncio
from g_tasks import g, Task


class T(Task):

    x = 1

    async def run(self):
        await asyncio.sleep(self.x)
        return self.x


import pytest

@pytest.mark.asyncio
async def test():
    print(await T())