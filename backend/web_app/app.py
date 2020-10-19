# -*- coding: utf-8 -*-
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.process import task_id

from common.settings import WS_PING_INTERVAL, WS_PING_TIMEOUT, AUTH_ENABLED, DEBUG
from common.log.journal import system_logger
from common.languages import lang_init

from common.database import start_gino, stop_gino
from common.veil.veil_api import get_veil_client, stop_veil_client
from common.veil.veil_redis import REDIS_POOL
from common.veil.veil_handlers import VdiTornadoGraphQLHandler

from web_app.thin_client.schema import thin_client_schema
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

localize = lang_init()

define("port", default=8888, help="port to listen on")
define("autoreload", default=True, help="autoreload application")
define("workers", default=1, help="num of process forks. 0 forks one process per cpu")

handlers = [
    (r'/controllers', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=controller_schema)),
    (r'/resources', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=resources_schema)),
    (r'/users', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
    (r'/groups', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=group_schema)),
    (r'/auth_dirs', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=auth_dir_schema)),
    (r'/pools', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=pool_schema)),
    (r'/events', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=event_schema)),
    (r'/tasks', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=task_schema)),
    (r'/thin_clients', VdiTornadoGraphQLHandler, dict(graphiql=True, schema=thin_client_schema)),
]

handlers += auth_api_urls
handlers += thin_client_api_urls
handlers += ws_event_monitoring_urls
handlers += license_api_urls


def make_app():
    # Autoreload mode is not compatible with the multi-process mode of HTTPServer.
    #  You must not give HTTPServer.start an argument other than 1 (or call tornado.process.fork_processes)
    #  if you are using autoreload mode.
    if options.workers == 1:
        autoreload = options.autoreload
    else:
        autoreload = False
    return Application(handlers,
                       debug=DEBUG,
                       websocket_ping_interval=WS_PING_INTERVAL,
                       websocket_ping_timeout=WS_PING_TIMEOUT,
                       autoreload=autoreload)


def init_license():
    return License()


def exit_handler(sig, frame):  # noqa
    io_loop = IOLoop.current()

    async def shutdown():
        REDIS_POOL.disconnect()
        await stop_veil_client()
        await stop_gino()
        io_loop.stop()

    io_loop.add_callback_from_signal(shutdown)


async def startup_alerts(vdi_license):
    """Выводим сообщения только в первом процессе. Если task_id None, значит процесс 1, если > 0, значит больше 1."""
    if not task_id():
        await system_logger.info(localize('VDI broker started with {} worker(s).').format(options.workers))
        # Проверка настроек
        if not AUTH_ENABLED:
            await system_logger.warning(localize('Authentication system is disabled.'))
        if vdi_license.expired:
            await system_logger.warning(
                localize('The license is expired. Some functions will be blocked. Contact your dealer.'))
        if DEBUG:
            await system_logger.warning(localize('DEBUG mode is enabled.'))


async def startup_server():
    """Запуск брокера."""
    options.parse_command_line()
    # signals
    init_signals(exit_handler)
    app = make_app()
    # Инициализация клиента
    get_veil_client()
    # Запуск tornado
    server = HTTPServer(app)
    server.listen(options.port)
    server.start(options.workers)
    # Инициализация лицензии
    vdi_license = init_license()
    # Инициализация БД
    await start_gino(app)
    # Вывод уведомлений
    await startup_alerts(vdi_license)


if __name__ == '__main__':
    # TODO: проверить запуск тестов
    IOLoop.current().run_sync(startup_server)
    IOLoop.current().start()
