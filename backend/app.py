# -*- coding: utf-8 -*-
import time
import signal

from tornado.ioloop import IOLoop
import tornado.web
import tornado.log
import tornado.options

from settings import DB_NAME, DB_PASS, DB_USER, DB_PORT, DB_HOST, WS_PING_INTERVAL, WS_PING_TIMEOUT, AUTH_ENABLED
from database import db
from common.veil_handlers import VdiTornadoGraphQLHandler

from journal.event.schema import event_schema
from auth.user_schema import user_schema
from auth.group_schema import group_schema
from auth.authentication_directory.auth_dir_schema import auth_dir_schema
from pool.schema import pool_schema
from vm.schema import vm_schema
from controller.schema import controller_schema
from controller_resources.schema import resources_schema

from vm.vm_manager import VmManager
from resources_monitoring.resources_monitor_manager import resources_monitor_manager
from pool.pool_task_manager import pool_task_manager

from auth.urls import auth_api_urls
from auth.license.urls import license_api_urls
from thin_client_api.urls import thin_client_api_urls
from resources_monitoring.urls import ws_event_monitoring_urls

from languages import lang_init
from journal.log.logging import Logging
from journal.journal import Log as log


_ = lang_init()

tornado.options.define("access_to_stdout", default=True, help="Log tornado.access to stdout")
tornado.options.define("port", default=8888, help="port to listen on")
tornado.options.define("autoreload", default=True, help="autoreload application")
tornado.options.define("debug", default=True, help="debug mode")

handlers = [
    (r'/controllers', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=controller_schema)),
    (r'/resources', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=resources_schema)),
    (r'/users', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
    (r'/groups', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=group_schema)),
    (r'/auth_dirs', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=auth_dir_schema)),
    (r'/vms', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=vm_schema)),
    (r'/pools', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=pool_schema)),
    (r'/events', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=event_schema)),
]

handlers += auth_api_urls
handlers += thin_client_api_urls
handlers += ws_event_monitoring_urls
handlers += license_api_urls


def init_signals():
    signal.signal(signal.SIGTERM, exit_handler)
    signal.signal(signal.SIGINT, exit_handler)  # KeyboardInterrupt


def init_callbacks():
    IOLoop.current().add_callback(resources_monitor_manager.start)
    IOLoop.current().add_callback(pool_task_manager.fill_start_data)


def init_tasks():
    vm_manager = VmManager()
    IOLoop.instance().add_timeout(time.time(), vm_manager.start)


def bootstrap():
    """Запускает логгирование"""
    init_signals()
    # uncomment for run without supervisor:
    # tornado.options.options.log_file_prefix = 'vdi_tornado.log'
    tornado.options.parse_command_line(final=True)
    Logging.init_logging(tornado.options.options.access_to_stdout)


def make_app():
    return tornado.web.Application(handlers,
                                   debug=tornado.options.options.debug,
                                   websocket_ping_interval=WS_PING_INTERVAL,
                                   websocket_ping_timeout=WS_PING_TIMEOUT,
                                   autoreload=tornado.options.options.autoreload)


async def start_gino():
    await db.set_bind(
        'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'.format(DB_USER=DB_USER, DB_PASS=DB_PASS,
                                                                                DB_HOST=DB_HOST, DB_PORT=DB_PORT,
                                                                                DB_NAME=DB_NAME))


async def stop_gino():
    await db.pop_bind().close()


def init_gino():
    IOLoop.current().run_sync(lambda: start_gino())


def start_server():
    log.name(_('Tornado VDI started'))

    if not AUTH_ENABLED:
        log.name(_('Auth is disabled. Enable on production!'))

    app = make_app()
    init_gino()
    app.listen(tornado.options.options.port)
    init_tasks()
    init_callbacks()
    IOLoop.current().start()


def exit_handler(sig, frame):
    IOLoop.instance().add_callback_from_signal(shutdown_server)


async def shutdown_server():
    log.name(_('Stopping Tornado VDI'))

    log.name(_('Stopping resources_monitor_manager'))
    await resources_monitor_manager.stop()

    log.name(_('Stopping GINO'))
    await stop_gino()

    log.name(_('Stopping IOLoop'))
    IOLoop.current().stop()

    log.name(_('Tornado VDI stopped'))


if __name__ == '__main__':
    bootstrap()
    start_server()
