# -*- coding: utf-8 -*-
from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.graphql import graphql


class ExecError(Exception):
    pass


async def execute_scheme(_schema, query, variables=None, context=None):
    r = await graphql(_schema, query, variables=variables, executor=AsyncioExecutor(), return_promise=True,
                      context=context)
    if r.errors:
        raise ExecError(repr(r.errors))
    return r.data
