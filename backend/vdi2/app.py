import tornado.ioloop
import tornado.web

from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler
from settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST  # , SECRET_KEY, PING_INTERVAL
from database import db
from controller.schema import controller_schema

from auth.urls import auth_urls
# from pool.urls import pool_urls

from auth.schema import user_schema

if __name__ == '__main__':
    handlers = [
        (r'/controllers', TornadoGraphQLHandler, dict(graphiql=True, schema=controller_schema)),
        (r'/users', TornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
        # (r'/graphql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema)),
        # (r'/graphql/batch', TornadoGraphQLHandler, dict(graphiql=True, schema=schema, batch=True)),
        # (r'/graphql/graphiql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema))
    ]

    handlers += auth_urls
    # handlers += pool_urls

    app = tornado.web.Application(handlers, debug=True)  # , websocket_ping_interval=PING_INTERVAL)  #, cookie_secret=SECRET_KEY)
    tornado.ioloop.IOLoop.current().run_sync(
        lambda: db.init_app(app,
                            host=DB_HOST,
                            port=DB_PORT,
                            user=DB_USER,
                            password=DB_PASS,
                            database=DB_NAME))
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
