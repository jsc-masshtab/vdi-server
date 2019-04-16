
from . import app

from starlette.graphql import GraphQLApp
from vdi.graphql.schema import schema
from graphql.execution.executors.asyncio import AsyncioExecutor

app.add_route('/admin', GraphQLApp(schema, executor_class=AsyncioExecutor))