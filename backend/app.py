import tornado.ioloop
import tornado.web

from graphene_tornado.tornado_graphql_handler import TornadoGraphQLHandler

from settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST, WS_PING_INTERVAL, WS_PING_TIMEOUT
from database import db
from common.veil_handlers import VdiTornadoGraphQLHandler

from vm.vm_manager import VmManager
from resources_monitoring.resources_monitor_manager import resources_monitor_manager

from auth.urls import auth_api_urls
from thin_client_api.urls import thin_client_api_urls
from resources_monitoring.urls import ws_event_monitoring_urls

from event.schema import event_schema
from user.schema import user_schema
from auth.schema import auth_dir_schema
from pool.schema import pool_schema
from vm.schema import vm_schema
from controller.schema import controller_schema
from controller_resources.schema import resources_schema

from pool.pool_task_manager import pool_task_manager

import time

# if __name__ == '__main__':

handlers = [
    (r'/controllers', TornadoGraphQLHandler, dict(graphiql=True, schema=controller_schema)),
    (r'/resources', TornadoGraphQLHandler, dict(graphiql=True, schema=resources_schema)),
    (r'/users', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
    (r'/auth_dirs', TornadoGraphQLHandler, dict(graphiql=True, schema=auth_dir_schema)),
    (r'/vms', TornadoGraphQLHandler, dict(graphiql=True, schema=vm_schema)),
    (r'/pools', TornadoGraphQLHandler, dict(graphiql=True, schema=pool_schema)),
    (r'/events', TornadoGraphQLHandler, dict(graphiql=True, schema=event_schema)),
    # (r'/graphql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema)),
    # (r'/graphql/batch', TornadoGraphQLHandler, dict(graphiql=True, schema=schema, batch=True)),
    # (r'/graphql/graphiql', TornadoGraphQLHandler, dict(graphiql=True, schema=schema))
]

handlers += auth_api_urls
handlers += thin_client_api_urls
handlers += ws_event_monitoring_urls

# import asyncio
# from common.utils import cancel_async_task
# async def test_co():
#
#     while True:
#         print('HELLOW')
#         await asyncio.sleep(1)

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

        tornado.ioloop.IOLoop.current().add_callback(pool_task_manager.fill_start_data)

        tornado.ioloop.IOLoop.current().start()

    except KeyboardInterrupt:
        print('Finish')
    finally:
        tornado.ioloop.IOLoop.current().run_sync(
            lambda: resources_monitor_manager.stop()
        )

        tornado.ioloop.IOLoop.instance().remove_timeout(vm_manager_task)
