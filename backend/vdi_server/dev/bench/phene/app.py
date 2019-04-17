
from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql.execution.executors.sync import SyncExecutor
from starlette.applications import Starlette
from starlette.graphql import GraphQLApp

from schema import schema

app = Starlette(debug=True)

app.add_route('/admin', GraphQLApp(schema, executor_class=AsyncioExecutor
                                   ))