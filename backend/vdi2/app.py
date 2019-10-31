import tornado.ioloop
import tornado.web

from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler
from settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST, WS_PING_INTERVAL

from database import db
from controller.schema import controller_schema
from controller_resources.schema import resources_schema

from thin_client_api.urls import thin_client_api_urls
from resources_monitoring.urls import ws_event_monitoring_urls

from auth.schema import user_schema

from resources_monitoring.resources_monitor_manager import resources_monitor_manager


if __name__ == '__main__':

    handlers = [
        (r'/controllers', TornadoGraphQLHandler, dict(graphiql=True, schema=controller_schema)),
        (r'/resources', TornadoGraphQLHandler, dict(graphiql=True, schema=resources_schema)),
        (r'/users', TornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
        # (r'/graphql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema)),
        # (r'/graphql/batch', TornadoGraphQLHandler, dict(graphiql=True, schema=schema, batch=True)),
        # (r'/graphql/graphiql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema))
    ]

    handlers += thin_client_api_urls
    handlers += ws_event_monitoring_urls

    app = tornado.web.Application(handlers, debug=True, websocket_ping_interval=WS_PING_INTERVAL)

    tornado.ioloop.IOLoop.current().run_sync(
        lambda: db.init_app(app,
                            host=DB_HOST,
                            port=DB_PORT,
                            user=DB_USER,
                            password=DB_PASS,
                            database=DB_NAME))
    app.listen(8888)

    try:
        tornado.ioloop.IOLoop.current().add_callback(resources_monitor_manager.start)
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print('Finish')
    finally:
        tornado.ioloop.IOLoop.current().run_sync(
            lambda: resources_monitor_manager.stop()
        )
