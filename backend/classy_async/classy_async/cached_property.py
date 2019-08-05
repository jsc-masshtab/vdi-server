from functools import wraps

from .asyncio_utils import Awaitable

#TODO this is better done with ContextVars directly
class CachedFunc(Awaitable):

    def __init__(self, func):
        self._wrapped_func = func

    def get_identity(self):
        return self._wrapped_func

    async def run(self, *args, **kwargs):
        return await self._wrapped_func(*args, **kwargs)


def cached(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await CachedFunc(func)

    return wrapper