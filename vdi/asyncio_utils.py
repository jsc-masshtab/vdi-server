import asyncio
from functools import wraps

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
                r = asyncio.CancelledError()
            r = fut.exception() or fut.result()
            results.pop().set_result(r)

        for task in awaitables:
            task.add_done_callback(on_done)

    def __aiter__(self):
        return self

    async def __anext__(self):
        while self.results:
            fut = self.results.pop()
            r = await fut
            return r
        raise StopAsyncIteration


def callback(async_fun):
    '''
    callbacks for futures are synchronous.
    This makes async function usable as a callback too.
    '''
    @wraps(async_fun)
    def wrapper(*args):
        asyncio.create_task(async_fun(*args))

    return wrapper