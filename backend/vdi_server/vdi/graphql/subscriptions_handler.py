import asyncio

import rx
from rx.core import Observable
from rx.internal import extensionmethod

from websockets.exceptions import ConnectionClosed as WsConnectionClosed

from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.execution.base import ExecutionResult
from graphql.error import format_error

from collections import OrderedDict
import json

from vdi.utils import print

from classy_async import g

class SubscriptionHandler:

    @classmethod
    async def handle(cls, websocket, schema):

        g.use_threadlocal(True)

        await websocket.accept()
        message = await websocket.receive()
        graphql_string = message['text']
        #print('graphql_string:', graphql_string)
        result = schema.execute(graphql_string, allow_subscriptions=True, executor=AsyncioExecutor())

        #  if subscription not found  the result is ExecutionResult
        if isinstance(result, ExecutionResult):
            await cls._prepare_data_and_send(result, websocket)
            await websocket.close()
            return

        # if subscription found the result is Observable
        iterator = await result.__aiter__()
        try:
            async for single_result in iterator:
                await cls._prepare_data_and_send(single_result, websocket)
            await websocket.close()

        except WsConnectionClosed:
            # stop observable
            iterator.dispose()

    @classmethod
    def _execution_result_to_dict(cls, execution_result):
        result = OrderedDict()
        result['data'] = execution_result.data if execution_result.data else None

        if execution_result.errors:
            result['errors'] = [format_error(error) for error in execution_result.errors]
        else:
            result['errors'] = None
        return result

    @classmethod
    async def _prepare_data_and_send(cls, single_result, websocket):
        # prepare data
        message_to_send = cls._execution_result_to_dict(single_result)
        json_message = json.dumps(message_to_send)
        # send data
        await websocket.send_json(json_message)


# Taken from https://github.com/ReactiveX/RxPY/blob/develop/examples/asyncio/toasynciterator.py
future_ctor = rx.config.get("Future") or asyncio.Future
@extensionmethod(Observable)
async def __aiter__(self):
    source = self

    class AIterator:
        def __init__(self):
            self.notifications = []
            self.future = future_ctor()

            self.disposable = source.materialize().subscribe(self.on_next)

        def feeder(self):
            if not self.notifications or self.future.done():
                return

            notification = self.notifications.pop(0)
            dispatch = {
                'N': lambda: self.future.set_result(notification.value),
                'E': lambda: self.future.set_exception(notification.exception),
                'C': lambda: self.future.set_exception(StopAsyncIteration)
            }

            dispatch[notification.kind]()

        def on_next(self, notification):
            self.notifications.append(notification)
            self.feeder()

        def dispose(self):
            self.disposable.dispose()

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.feeder()

            value = await self.future
            self.future = future_ctor()
            return value

    return AIterator()