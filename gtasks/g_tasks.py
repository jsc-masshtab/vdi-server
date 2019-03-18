
import threading
import asyncio
import contextvars
from functools import wraps

local_ctx = threading.local()
local_ctx.use_me = False
local_ctx.g = {}

class Context:
    _values = contextvars.ContextVar('values')
    _tasks = contextvars.ContextVar('tasks')

    @property
    def values(self):
        var = self._values
        if local_ctx.use_me:
            return local_ctx.g[var]
        return var.get()

    # @values.setter
    # def values(self, value):
    #     var = self._values
    #     if local_ctx.use_me:
    #         local_ctx.g[var] = value
    #     var.set(value)

    @property
    def tasks(self):
        var = self._tasks
        if local_ctx.use_me:
            return local_ctx.g[var]
        return var.get()


    # @tasks.setter
    # def tasks(self, value):
    #     var = self._tasks
    #     if local_ctx.use_me:
    #         local_ctx.g[var] = value
    #     var.set(value)

    def use_threadlocal(self, yes=True):
        local_ctx.use_me = yes
        try:
            g.tasks
        except LookupError:
            local_ctx.g[self._tasks] = {}
            local_ctx.g[self._values] = {}

    def __getattr__(self, item):
        return self.values[item]

    def set_attr(self, key, value):
        self.values[key] = value

    def init(self):
        self._values.set({})
        self._tasks.set({})




g = Context()

# a decorator
def task(co):
    @wraps(co)
    def wrapper(*args): # co should not have parameters
        # args can be only [self]
        if not args:
            return Task.from_co(co)

        async def new_co():
            return (await co(*args))

        return Task.from_co(new_co)

    return wrapper

class Task:

    _source = 'class'

    def __await__(self):
        return self.ensure_task().__await__()

    @classmethod
    def from_co(cls, f):
        # TODO check no params
        obj = cls()
        obj._co = f
        obj._source = 'co'
        return obj

    @property
    def id(self):
        if self._source == 'class':
            return self.__class__
        assert self._source == 'co'
        return self._co

    @property
    def co(self):
        if self._source == 'class':
            return self.run
        assert self._source == 'co'
        return self._co

    def ensure_task(self):
        tasks = g.tasks
        if self.id in tasks:
            return tasks[self.id]
        task = asyncio.create_task(self.co())
        task = asyncio.shield(task)
        tasks[self.id] = task
        return task

    # async def fresh_context(self):
    #     g.init()
    #     return (await self)
    #

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)