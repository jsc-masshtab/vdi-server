import inspect
from functools import wraps


class Unset:
    pass


def with_self(f):
    if not inspect.iscoroutinefunction(f):
        raise NotImplementedError
        # @wraps(f)
        # def wrapper(self, *args, **kwargs):
        #     with self:
        #         return f(self, *args, **kwargs)

        # return wrapper

    @wraps(f)
    async def wrapper(self, *args, **kwargs):
        self.rerun_cause = None
        with self:
            result = await f(self, *args, **kwargs)
        while self.rerun_cause:
            self.rerun_cause = None
            with self:
                result = await f(self, *args, **kwargs)

        return result


    return wrapper
