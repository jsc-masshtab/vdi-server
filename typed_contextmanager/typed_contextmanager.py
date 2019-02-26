
import inspect
import typing
from contextlib import contextmanager, asynccontextmanager, AbstractAsyncContextManager
from functools import wraps

from cached_property import cached_property as cached

from dataclasses import dataclass

from typing import Union, List

function = type(lambda: 0)


def typed_contextmanager(f):
    return_type = f.__annotations__.get('return')
    if not inspect.isasyncgenfunction(f):
        cm_func = contextmanager(f)
        is_async = False
    else:
        cm_func = asynccontextmanager(f)
        is_async = True

    @wraps(f)
    def wrapper(*args, **kwargs):
        if is_async:
            async def get_context(t):
                return cm_func(*args, **kwargs)
        else:
            get_context = lambda t: cm_func(*args, **kwargs)

        return CMInfo(
            get_context=get_context,
            context_types=(return_type,),
            is_async=is_async,
        )

    return wrapper


def type_union_factory(f):
    sig = inspect.signature(f)
    for name, param in sig.parameters.items():
        try:
            if param.annotation.__origin__ is Union:
                context_types = param.annotation.__args__
                break
        except AttributeError:
            continue
    else:
        assert 0
    new_params = dict(sig.parameters)
    del new_params[name]
    sig = inspect.Signature(new_params.values())


    @wraps(f)
    def wrapper(*args, **kwargs):
        params = sig.bind(*args, **kwargs).arguments

        def get_cm(context_type):
            params[name] = context_type
            result = f(**params)
            if isinstance(result, CMInfo):
                return result.get_context(context_type)
            return result

        return CMInfo(
            get_context=get_cm,
            context_types=context_types
        )

    return wrapper


typed_contextmanager.factory = type_union_factory

@dataclass()
class CMInfo:
    get_context: function
    context_types: List[type]
    is_async: bool

    def __call__(self, target):
        if self.is_async:
            print('!Sync')
            return AsyncTargetWrapper(
                get_context=self.get_context,
                context_types=self.context_types,
                target=target
            )
        print('Sync')
        return SyncTargetWrapper(
            get_context=self.get_context,
            context_types=self.context_types,
            target=target
        )


@dataclass()
class TargetWrapper:
    get_context: function
    context_types: List[type]
    target: function = None

    @cached
    def context_type(self):
        self.context_param
        return self._type

    @cached
    def context_param(self):
        sig = inspect.signature(self.target)
        for name, param in sig.parameters.items():
            for t in self.context_types:
                if issubclass(t, param.annotation):
                    self._type = t # TODO
                    return param

    @cached
    def signature(self):
        sig = inspect.signature(self.target)
        params = dict(sig.parameters)
        del params[self.context_param.name]
        return inspect.Signature(params)


class SyncTargetWrapper(TargetWrapper):

    def __call__(self, *args, **kwargs):
        with self.get_context(self.context_type) as ctx:
            params = self.signature.bind(*args, **kwargs).arguments
            params[self.context_param.name] = ctx
            return self.target(**params)


class AsyncTargetWrapper(TargetWrapper):

    async def __call__(self, *args, **kwargs):
        mgr = await self.get_context(self.context_type)
        async with mgr as ctx:
            params = self.signature.bind(*args, **kwargs).arguments
            params[self.context_param.name] = ctx
            result = await self.target(**params)
            return result
