import asyncio
from functools import wraps
from typing import List

from cached_property import cached_property as cached
#from dataclasses import dataclass # 3.7
from async_generator import async_generator, yield_, asynccontextmanager


#from .g_tasks import g # python 3.7

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

    # python 3.7
    # async def items(self):
    #     """
    #     Include the identities for awaitables:
    #     for iden, result in wait(*tasks):
    #       ...
    #     """
    #     while self.results:
    #         fut = self.results.pop()
    #         yield await fut
    #
    # async def __aiter__(self):
    #     async for key, result in self.items():
    #         yield result
    # python 3.5
    @async_generator
    async def items(self):
        """
        Include the identities for awaitables:
        for iden, result in wait(*tasks):
          ...
        """
        while self.results:
            fut = self.results.pop()
            fut_result = await fut
            await yield_(fut_result)

    @async_generator
    async def __aiter__(self):
        async for key, result in self.items():
            await yield_(result)

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


    # result_list = list()
    # iterator = (wait(*args, **kwargs))
    # iterator = type(iterator).__aiter__(iterator)
    # running = True
    # while running:
    #     try:
    #         result = await type(iterator).__anext__(iterator)
    #     except StopAsyncIteration:
    #         running = False
    #     else:
    #         result_list.append(result)
    #
    # return result_list

#@async_generator
async def wait_all(*args, **kwargs):

    #python 3.7
    # return [
    #    result async for result in wait(*args, **kwargs)
    # ]

    #3.5
    # async inside comprohension is not supported
    result_list = []
    async for result in wait(*args, **kwargs):
        result_list.append(result)
    return result_list

@async_generator
async def load_json_lines(stream_reader):
    async for line in stream_reader:
        await yield_(line)

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
        loop = asyncio.get_event_loop()
        async_task = loop.create_task(self.co())
        return async_task
        #return asyncio.create_task(self.co()) # python 3.7

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

#@dataclass()
class TaskTimeout(Exception):

    def __init__(self, task: type):
        self.task = task
    #task: type # python 3.7


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
        #tasks = g.tasks
        #if self.cache_result and self.serialized in tasks:
        #    return tasks[self.serialized]
        #task = asyncio.create_task(self.co())
        # task = asyncio.shield(task)
        #if self.cache_result:
        #    tasks[self.serialized] = task
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.co())
        task = asyncio.shield(task)
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