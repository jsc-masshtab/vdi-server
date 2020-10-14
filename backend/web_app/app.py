# -*- coding: utf-8 -*-
from tornado.ioloop import IOLoop
import tornado.web
import tornado.options

from common.settings import WS_PING_INTERVAL, WS_PING_TIMEOUT, AUTH_ENABLED, DEBUG
from common.log.journal import system_logger
from common.languages import lang_init

from common.database import start_gino, stop_gino
from common.veil.veil_api import get_veil_client, stop_veil_client
from common.veil.veil_redis import REDIS_POOL
from common.veil.veil_handlers import VdiTornadoGraphQLHandler

from web_app.task.schema import task_schema
from web_app.journal.schema import event_schema
from web_app.auth.license.utils import License
from web_app.auth.user_schema import user_schema
from web_app.auth.group_schema import group_schema
from web_app.auth.authentication_directory.auth_dir_schema import auth_dir_schema
from web_app.pool.schema import pool_schema
from web_app.controller.schema import controller_schema
from web_app.controller.resource_schema import resources_schema

from web_app.auth.urls import auth_api_urls
from web_app.auth.license.urls import license_api_urls
from web_app.thin_client_api.urls import thin_client_api_urls
from web_app.front_ws_api.urls import ws_event_monitoring_urls

from common.utils import init_signals

_ = lang_init()
# TODO: rename _ to localization, localize or smth similar

tornado.options.define("port", default=8888, help="port to listen on")
tornado.options.define("autoreload", default=True, help="autoreload application")
tornado.options.define("workers", default=1, help="num of process forks. 0 forks one process per cpu")

handlers = [
    (r'/controllers', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=controller_schema)),
    (r'/resources', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=resources_schema)),
    (r'/users', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
    (r'/groups', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=group_schema)),
    (r'/auth_dirs', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=auth_dir_schema)),
    (r'/pools', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=pool_schema)),
    (r'/events', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=event_schema)),
    (r'/tasks', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=task_schema)),
]

handlers += auth_api_urls
handlers += thin_client_api_urls
handlers += ws_event_monitoring_urls
handlers += license_api_urls


def make_app():
    return tornado.web.Application(handlers,
                                   debug=DEBUG,
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
    # log.name(_('Stopping Tornado VDI'))

    # log.name(_('Stopping redis'))
    REDIS_POOL.disconnect()

    # log.name(_('Stopping GINO'))
    await stop_gino()

    # log.name(_('Stopping client'))
    await stop_veil_client()

    # log.name(_('Stopping IOLoop'))
    IOLoop.current().stop()

    # log.name(_('Tornado VDI stopped'))


def start_server():
    tornado.options.parse_command_line(final=True)
    init_signals(exit_handler)

    app = make_app()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(tornado.options.options.port)
    server.start(tornado.options.options.workers)

    system_logger._debug('Tornado VDI started!')

    try:
        system_logger._debug('Checking veil-api-client...')
        get_veil_client()
    except Exception as E:  # noqa
        print(E)
        system_logger._debug('Can`t import VeiL client Singleton. Something goes wrong')
    else:
        system_logger._debug('No veil-api-client issues found.')

    if not AUTH_ENABLED:
        system_logger._debug(_('Auth is disabled. Enable on production!'))

    vdi_license = init_license()
    if vdi_license.expired:
        system_logger._debug(_('The license is expired. Some functions will be blocked. Contact your dealer.'))

    # log.name(_('License status: {}, expiration time: {}, thin clients limit: {}').format(
    #     not vdi_license.expired,
    #     vdi_license.expiration_date,
    #     vdi_license.thin_clients_limit))
    init_gino()
    IOLoop.current().start()


if __name__ == '__main__':
    from common.models.pool import Pool
    print('Pool.PoolConnectionTypes.SPICE: ', Pool.PoolConnectionTypes.SPICE)
    start_server()
