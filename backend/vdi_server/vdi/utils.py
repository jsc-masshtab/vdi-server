import inspect
from functools import wraps


def with_self(f):
    if not inspect.iscoroutinefunction(f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            with self:
                return f(self, *args, **kwargs)

        return wrapper

    @wraps(f)
    async def wrapper(self, *args, **kwargs):
        with self:
            return await f(self, *args, **kwargs)

    return wrapper
