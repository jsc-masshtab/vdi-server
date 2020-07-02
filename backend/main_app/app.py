# -*- coding: utf-8 -*-
from tornado.ioloop import IOLoop
import tornado.web
import tornado.log
import tornado.options

from settings import WS_PING_INTERVAL, WS_PING_TIMEOUT, AUTH_ENABLED
from database import start_gino, stop_gino
from redis_broker import REDIS_POOL
from common.veil_handlers import VdiTornadoGraphQLHandler

from journal.event.schema import event_schema
from auth.license.utils import License
from auth.user_schema import user_schema
from auth.group_schema import group_schema
from auth.authentication_directory.auth_dir_schema import auth_dir_schema
from pool.schema import pool_schema
from vm.schema import vm_schema
from controller.schema import controller_schema
from controller_resources.schema import resources_schema


from auth.urls import auth_api_urls
from auth.license.urls import license_api_urls
from thin_client_api.urls import thin_client_api_urls
from front_ws_api.urls import ws_event_monitoring_urls

from common.utils import init_signals

from languages import lang_init
from journal.log.logging import Logging
from journal.journal import Log as log


_ = lang_init()

tornado.options.define("access_to_stdout", default=True, help="tornado.access to stdout")
tornado.options.define("port", default=8888, help="port to listen on")
tornado.options.define("autoreload", default=True, help="autoreload application")
tornado.options.define("debug", default=True, help="debug mode")
tornado.options.define("workers", default=1, help="num of process forks. 0 forks one process per cpu")

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


def make_app():
    return tornado.web.Application(handlers,
                                   debug=tornado.options.options.debug,
                                   websocket_ping_interval=WS_PING_INTERVAL,
                                   websocket_ping_timeout=WS_PING_TIMEOUT,
                                   autoreload=tornado.options.options.autoreload)


def init_gino():
    IOLoop.current().run_sync(lambda: start_gino())


def init_license():
    return License()


def exit_handler(sig, frame):
    IOLoop.instance().add_callback_from_signal(shutdown_server)


async def shutdown_server():
    log.name(_('Stopping Tornado VDI'))

    log.name(_('Stopping redis'))
    REDIS_POOL.disconnect()

    log.name(_('Stopping GINO'))
    await stop_gino()

    log.name(_('Stopping IOLoop'))
    IOLoop.current().stop()

    log.name(_('Tornado VDI stopped'))


def start_server():

    tornado.options.parse_command_line(final=True)
    Logging.init_logging(tornado.options.options.access_to_stdout)
    init_signals(exit_handler)

    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(tornado.options.options.port)
    server.start(tornado.options.options.workers)

    log.name(_('Tornado VDI started'))

    if not AUTH_ENABLED:
        log.general(_('Auth is disabled. Enable on production!'))

    vdi_license = init_license()
    if vdi_license.expired:
        log.general(_('The license is expired. Some functions will be blocked. Contact your dealer.'))

    log.name(_('License status: {}, expiration time: {}, thin clients limit: {}').format(
        not vdi_license.expired,
        vdi_license.expiration_date,
        vdi_license.thin_clients_limit))

    init_gino()

    IOLoop.current().start()


if __name__ == '__main__':
    start_server()
