import tornado.ioloop
import tornado.web

from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler

from auth.schema import user_schema
from common.veil_handlers import VdiTornadoGraphQLHandler
from common.utils import cancel_async_task
from event.schema import event_schema
from pool.schema import pool_schema
from vm.schema import vm_schema
from controller.schema import controller_schema
from controller_resources.schema import resources_schema

from vm.vm_manager import VmManager
from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from resources_monitoring.urls import ws_event_monitoring_urls
from thin_client_api.urls import thin_client_api_urls
from settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST, WS_PING_INTERVAL, WS_PING_TIMEOUT
from database import db

import time

# if __name__ == '__main__':

handlers = [
    (r'/controllers', TornadoGraphQLHandler, dict(graphiql=True, schema=controller_schema)),
    (r'/resources', TornadoGraphQLHandler, dict(graphiql=True, schema=resources_schema)),
    (r'/users', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
    (r'/vms', TornadoGraphQLHandler, dict(graphiql=True, schema=vm_schema)),
    (r'/pools', TornadoGraphQLHandler, dict(graphiql=True, schema=pool_schema)),
    (r'/events', TornadoGraphQLHandler, dict(graphiql=True, schema=event_schema)),
    # (r'/graphql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema)),
    # (r'/graphql/batch', TornadoGraphQLHandler, dict(graphiql=True, schema=schema, batch=True)),
    # (r'/graphql/graphiql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema))
]

handlers += thin_client_api_urls
handlers += ws_event_monitoring_urls

app = tornado.web.Application(handlers, debug=True, websocket_ping_interval=WS_PING_INTERVAL,
                              websocket_ping_timeout=WS_PING_TIMEOUT)

if __name__ == '__main__':
    tornado.ioloop.IOLoop.current().run_sync(
        lambda: db.init_app(app,
                            host=DB_HOST,
                            port=DB_PORT,
                            user=DB_USER,
                            password=DB_PASS,
                            database=DB_NAME))

    app.listen(8888)

    try:
        vm_manager = VmManager()
        vm_manager_task = tornado.ioloop.IOLoop.instance().add_timeout(time.time(), vm_manager.start)

        tornado.ioloop.IOLoop.current().add_callback(resources_monitor_manager.start)

        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print('Finish')
    finally:
        tornado.ioloop.IOLoop.current().run_sync(
            lambda: resources_monitor_manager.stop()
        )

        tornado.ioloop.IOLoop.instance().remove_timeout(vm_manager_task)
