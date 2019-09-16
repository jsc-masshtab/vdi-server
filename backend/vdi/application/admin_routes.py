from vdi.graphql_api.subscriptions_handler import SubscriptionHandler

from .app import app

from starlette.graphql import (
    GraphQLApp as _GraphQLApp,
    Request, Response, PlainTextResponse, status, BackgroundTasks, JSONResponse, format_graphql_error
)
from starlette.authentication import UnauthenticatedUser
from vdi.graphql_api.schema import schema
from graphql.execution.executors.asyncio import AsyncioExecutor

from vdi.errors import BackendError
from vdi.log import RequestsLog
from vdi.application import Request

def get_from_chain(ex, kind, limit=5):
    """
    Get exception of given lind (argument to isinstance) from the exception chain
    """
    for i in range(limit):
        if not ex:
            return None
        if isinstance(ex, kind):
            return ex
        ex = ex.__context__

    return None


class GraphQLApp(_GraphQLApp):

    def format_graphql_error(self, err):
        original_error = getattr(err, 'original_error', None)
        backend_error = get_from_chain(original_error, BackendError)
        if backend_error:
            return backend_error.format_error()
        return format_graphql_error(err)

    async def result_hook(self, result):
        if not result.data:
            #FIXME
            return
        if 'requests' in result.data:
            stub = result.data['requests'][0]
            requests = await RequestsLog()
            for req in requests:
                req['time'] = "{:.2f}".format(req['time'])
            result.data['requests'] = [
                {k: v for k, v in req.items() if k in stub}
                for req in requests
            ]

    # This is copied from its ancestor
    async def handle_graphql(self, request: Request) -> Response:
        if request.method in ("GET", "HEAD"):
            if "text/html" in request.headers.get("Accept", ""):
                if not self.graphiql:
                    return PlainTextResponse(
                        "Not Found", status_code=status.HTTP_404_NOT_FOUND
                    )
                return await self.handle_graphiql(request)

            data = request.query_params  # type: typing.Mapping[str, typing.Any]

        elif request.method == "POST":
            content_type = request.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = await request.json()
            elif "application/graphql" in content_type:
                body = await request.body()
                text = body.decode()
                data = {"query": text}
            elif "query" in request.query_params:
                data = request.query_params
            else:
                return PlainTextResponse(
                    "Unsupported Media Type",
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

        else:
            return PlainTextResponse(
                "Method Not Allowed", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        try:
            query = data["query"]
            variables = data.get("variables")
            operation_name = data.get("operationName")
        except KeyError:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        background = BackgroundTasks()
        context = {"request": request, "background": background}

        result = await self.execute(
            query, variables=variables, context=context, operation_name=operation_name
        )
        await self.result_hook(result)
        error_data = (
            [self.format_graphql_error(err) for err in result.errors]
            if result.errors
            else None
        )
        response_data = {"data": result.data, "errors": error_data}
        status_code = (
            status.HTTP_400_BAD_REQUEST if result.errors else status.HTTP_200_OK
        )

        return JSONResponse(
            response_data, status_code=status_code, background=background
        )



app.add_route('/admin', GraphQLApp(schema, executor_class=AsyncioExecutor))


# subscriptions
# @app.websocket_route('/subscriptions')
# async def subscriptions_ws_endpoint(websocket):
#     await SubscriptionHandler.handle(websocket, schema)
