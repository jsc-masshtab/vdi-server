
import pytest

from vdi.asyncio_utils import Awaitable

class Task(Awaitable):

    def __init__(self, *, artifact=None):
        self.artifact = artifact

    async def run(self):
        return self.artifact

@pytest.mark.asyncio
async def test():
    r = await Task(artifact=42)
    assert r == 42
