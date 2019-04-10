
import inspect
from dataclasses import dataclass

from contextlib import AbstractContextManager, AbstractAsyncContextManager

from functools import wraps

from typing import Union

function = type(lambda: None)

@dataclass()
class enter_context:
    mgr_factory: function

    def __call__(self, f: function):
        if not inspect.iscoroutinefunction(f):
            @wraps(f)
            def wrapper(*args, **kw):
                with self.mgr_factory() as ctx:
                    return f(ctx, *args, **kw)

            return wrapper

        @wraps(f)
        async def wrapper(*args, **kw):
            mgr = self.mgr_factory()
            if isinstance(mgr, AbstractContextManager):
                with mgr as ctx:
                    return await f(ctx, *args, **kw)

            async with mgr as ctx:
                return await f(ctx, *args, **kw)

        return wrapper