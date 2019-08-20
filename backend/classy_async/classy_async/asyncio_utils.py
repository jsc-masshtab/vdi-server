import asyncio
from functools import wraps
from typing import List

from cached_property import cached_property as cached
from dataclasses import dataclass

from .g_tasks import g

def list(gen_func):
    return list(gen_func())

function = type(lambda: None)

import inspect

class wait:
    '''
    Async iterator, constructed from a list of awaitables.
    Returns results or exceptions as soon as they are ready.
    '''

    @cached
    def results(self):
        # We await on these in __aiter__
        loop = asyncio.events.get_event_loop()
        return [
            loop.create_future() for _ in self.awaitables
        ]

    def __init__(self, *awaitables, suppress_exceptions=False, **kwargs):
        self.suppress_exceptions = suppress_exceptions
        if not awaitables and kwargs:
            self.awaitables = kwargs.items()
        else:
            self.awaitables = [
                (self.get_identity(task), task) for task in awaitables
            ]

        results = self.results[:]

        for key, src in self.awaitables:
            def cb(fut, key=key):
                target = results.pop()
                # if not fut.cancelled() and not fut.exception():
                #     result = (key, fut.result())
                #     target.set_result(result)
                # else:
                self.copy_result(fut, target, key)

            src = asyncio.ensure_future(src)
            src.add_done_callback(cb)


    async def items(self):
        """
        Include the identities for awaitables:
        for iden, result in wait(*tasks):
          ...
        """
        while self.results:
            fut = self.results.pop()
            yield await fut

    async def __aiter__(self):
        async for key, result in self.items():
            yield result

    def copy_result(self, fut, target, key):
        # Copies the result of one future to another
        #
        if fut.cancelled():
            r = asyncio.CancelledError()  # ?
            target.set_result(r)
            return
        r = fut.exception()
        if r:
            if not self.suppress_exceptions:
                target.set_exception(r)
            else:
                r = (key, r)
                target.set_result(r)
            return
        r = fut.result()
        r = (key, r)
        target.set_result(r)

    def get_identity(self, awaitable):
        if hasattr(awaitable, 'get_identity'):
            return awaitable.get_identity()
        if inspect.iscoroutine(awaitable):
            return awaitable.__name__
        if isinstance(awaitable, asyncio.Task):
            coro = awaitable._coro
            return self.get_identity(coro)
        raise NotImplementedError


async def wait_all(*args, **kwargs):
    return [
        result async for result in wait(*args, **kwargs)
    ]


class Awaitable:
    """
    Class-based coroutine.
    The main coroutine is called run
    """

    timeout = None

    def cancel(self):
        self.task.cancel()

    def co(self):
        if self.timeout:
            return self.run_with_timeout(self.timeout)
        return self.run()

    @cached
    def type(self):
        return self.__class__

    def get_identity(self):
        return self.type

    @cached
    def task(self):
        return asyncio.create_task(self.co())

    def __await__(self):
        return self.task.__await__()

    async def run(self):
        raise NotImplementedError

    async def run_with_timeout(self, seconds):
        tasks = {
            'main': asyncio.ensure_future(self.run()),
            'timeout': asyncio.ensure_future(asyncio.sleep(seconds)),
        }
        async for key, result in wait(**tasks).items():
            if key == 'timeout':
                tasks['main'].cancel()
                raise TaskTimeout(self.type)
            tasks['timeout'].cancel()
            return result


Wait = wait

@dataclass()
class TaskTimeout(Exception):
    task: type


class Task(Awaitable):

    # g_tasks.Task v2

    @cached
    def init_kwargs(self):
        kwargs = dict(self.__dict__)
        if 'run' in kwargs and callable(kwargs['run']):
            del kwargs['run']
        return kwargs

    def __post_init__(self):
        # if is a dataclass
        self.init_kwargs

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.init_kwargs


    @cached # frozen?
    def serialized(self):
        data = dict(type=self.type, **self.init_kwargs)
        return tuple(data.items())

    @cached
    def task(self):
        tasks = g.tasks
        if self.cache_result and self.serialized in tasks:
            return tasks[self.serialized]
        task = asyncio.create_task(self.co())
        task = asyncio.shield(task)
        if self.cache_result:
            tasks[self.serialized] = task
        return task

    cache_result = True


def timeout(seconds):
    return task(timeout=seconds)

def task(timeout=None):
    def decorate(f):
        @wraps(f)
        async def wrapper(*args, **kw):
            async def run():
                return await f(*args, **kw)

            task = Awaitable()
            task.timeout = timeout
            task.type = f
            task.run = run
            return await task

        return wrapper

    return decorate