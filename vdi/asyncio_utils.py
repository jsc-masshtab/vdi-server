import asyncio
from functools import wraps

from cached_property import cached_property as cached
from dataclasses import dataclass


class Wait:
    '''
    Async iterator, constructed from a list of awaitables.
    Returns results or exceptions as soon as they are ready.
    '''

    def __init__(self, *awaitables):
        loop = asyncio.events.get_event_loop()
        awaitables = [
            asyncio.tasks.ensure_future(aw) for aw in awaitables
        ]
        self.results = [
            loop.create_future()
            for _ in awaitables
        ]

        def on_done(fut, results=self.results[:]):
            if fut.cancelled():
                r = asyncio.CancelledError() # ?
            else:
                r = fut
            results.pop().set_result(r)

        for task in awaitables:
            task.add_done_callback(on_done)

    def __aiter__(self):
        return self

    async def __anext__(self):
        async for r, task in self.items():
            return r
        raise StopIteration

    async def items(self):
        while self.results:
            fut = self.results.pop()
            awaited = await fut
            r = awaited.exception() or awaited.result()
            print('!:', r, awaited)
            yield (r, awaited)



def callback(async_fun):
    '''
    callbacks for futures are synchronous.
    This makes async function usable as a callback too.
    '''
    @wraps(async_fun)
    def wrapper(*args):
        asyncio.create_task(async_fun(*args))

    return wrapper

async def sleep(n):
    n = int(n)
    for i in range(n):
        await asyncio.sleep(1)
        print('.', end='')
    print()


class Awaitable:
    """
    Class-based coroutine.
    The main coroutine is called run
    """

    def cancel(self):
        self.task.cancel()

    @cached
    def task(self):
        t = asyncio.create_task(self.run())
        t.type = self.__class__
        return t

    def __await__(self):
        return self.task.__await__()

    async def run(self):
        raise NotImplementedError


    async def timeout(self, seconds):
        sleep_task = Sleep(seconds)

        async for result in Wait(self, sleep_task):
            if isinstance(result, Sleep.Result):
                self.task.cancel()
                raise TaskTimeout(self.__class__)
            sleep_task.cancel()
            return result


@dataclass()
class TaskTimeout(Exception):
    task: type


@dataclass()
class Sleep(Awaitable):
    timeout: float

    class Result:
        pass

    async def run(self):
        await asyncio.sleep(self.timeout)
        return self.Result()