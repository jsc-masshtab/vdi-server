import time
import sys
import logging
import signal

from tornado.ioloop import IOLoop
import tornado.web

import tornado.log
import tornado.options

from settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST, WS_PING_INTERVAL, WS_PING_TIMEOUT
from database import db
from common.veil_handlers import VdiTornadoGraphQLHandler

from event.schema import event_schema
from user.schema import user_schema
from auth.schema import auth_dir_schema
from pool.schema import pool_schema
from vm.schema import vm_schema
from controller.schema import controller_schema
from controller_resources.schema import resources_schema

from vm.vm_manager import VmManager
from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from pool.pool_task_manager import pool_task_manager

from auth.urls import auth_api_urls
from thin_client_api.urls import thin_client_api_urls
from resources_monitoring.urls import ws_event_monitoring_urls


logger = logging.getLogger(__name__)
tornado.options.define("access_to_stdout", default=False, help="Log tornado.access to stdout")
tornado.options.define("port", default=8888, help="port to listen on")
tornado.options.define("autoreload", default=True, help="autoreload application")
tornado.options.define("debug", default=True, help="debug mode")

handlers = [
    (r'/controllers', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=controller_schema)),
    (r'/resources', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=resources_schema)),
    (r'/users', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
    (r'/auth_dirs', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=auth_dir_schema)),
    (r'/vms', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=vm_schema)),
    (r'/pools', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=pool_schema)),
    (r'/events', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=event_schema)),
]

handlers += auth_api_urls
handlers += thin_client_api_urls
handlers += ws_event_monitoring_urls

app = tornado.web.Application(handlers,
                              debug=tornado.options.options.debug,
                              websocket_ping_interval=WS_PING_INTERVAL,
                              websocket_ping_timeout=WS_PING_TIMEOUT,
                              autoreload=tornado.options.options.autoreload)


def init_logging(access_to_stdout=False):
    if access_to_stdout:
        access_log = logging.getLogger('tornado.access')
        access_log.propagate = False
        access_log.setLevel(logging.INFO)
        stdout_handler = logging.StreamHandler(sys.stdout)
        access_log.addHandler(stdout_handler)


def init_signals():
    signal.signal(signal.SIGTERM, exit_handler)
    signal.signal(signal.SIGINT,  exit_handler)  # KeyboardInterrupt


def init_callbacks():
    IOLoop.current().add_callback(resources_monitor_manager.start)
    IOLoop.current().add_callback(pool_task_manager.fill_start_data)


def init_tasks():
    vm_manager = VmManager()
    IOLoop.instance().add_timeout(time.time(), vm_manager.start)


def bootstrap():
    """Запускает логгирование"""
    init_signals()
    # tornado.options.options.log_file_prefix = 'vdi_tornado.log'  # TODO: uncomment for run without supervisor.
    tornado.options.parse_command_line(final=True)
    init_logging(tornado.options.options.access_to_stdout)


def start_server():
    logger.info('Tornado VDI started')
    IOLoop.current().run_sync(
        lambda: db.init_app(app,
                            host=DB_HOST,
                            port=DB_PORT,
                            user=DB_USER,
                            password=DB_PASS,
                            database=DB_NAME))

    app.listen(tornado.options.options.port)
    init_tasks()
    init_callbacks()
    IOLoop.current().start()


def exit_handler(sig, frame):
    IOLoop.instance().add_callback_from_signal(shutdown_server)


async def shutdown_server():
    logger.info('Stopping Tornado VDI')

    logger.info('Stopping resources_monitor_manager')
    await resources_monitor_manager.stop()

    logger.info('Stopping IOLoop')
    IOLoop.current().stop()

    logger.info('Tornado VDI stopped')


if __name__ == '__main__':
    bootstrap()
    start_server()