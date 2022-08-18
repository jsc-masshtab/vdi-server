# -*- coding: utf-8 -*-
import socket
import ssl

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.process import task_id
from tornado.web import Application

from common.database import start_gino, stop_gino
from common.languages import _local_
from common.log.journal import system_logger
from common.models.license import License
from common.settings import (
    AUTH_ENABLED,
    DEBUG,
    SSL_CRT_FPATH,
    SSL_KEY_FPATH,
    WS_PING_INTERVAL,
    WS_PING_TIMEOUT,
)
from common.utils import init_signals
from common.veil.veil_api import get_veil_client_singleton, stop_veil_client
from common.veil.veil_handlers import VdiTornadoGraphQLHandler
from common.veil.veil_redis import redis_deinit, redis_init

from web_app.auth.authentication_directory.auth_dir_schema import auth_dir_schema
from web_app.auth.group_schema import group_schema
from web_app.auth.license.urls import license_api_urls
from web_app.auth.urls import auth_api_urls
from web_app.auth.user_schema import user_schema
from web_app.controller.resource_schema import resources_schema
from web_app.controller.schema import controller_schema
from web_app.front_ws_api.urls import ws_event_monitoring_urls
from web_app.info.schema import broker_info_schema
from web_app.journal.schema import event_schema
from web_app.pool.schema import pool_schema
from web_app.settings.schema import settings_schema
from web_app.statistics.schema import statistics_schema
from web_app.task.schema import task_schema
from web_app.thin_client_api.schema import thin_client_schema
from web_app.thin_client_api.urls import thin_client_api_urls

define("port", default=8888, help="port to listen on")
define("address", default="127.0.0.1", help="address to listen on")
define("autoreload", default=True, help="autoreload application")
define("workers", default=1, help="num of process forks. 0 forks one process per cpu")
define("ssl", default=False, help="force https")

handlers = [
    (
        r"/controllers",
        VdiTornadoGraphQLHandler,
        dict(graphiql=True, schema=controller_schema),
    ),
    (
        r"/resources",
        VdiTornadoGraphQLHandler,
        dict(graphiql=True, schema=resources_schema),
    ),
    (r"/users", VdiTornadoGraphQLHandler, dict(graphiql=True, schema=user_schema)),
    (r"/groups", VdiTornadoGraphQLHandler, dict(graphiql=True, schema=group_schema)),
    (
        r"/auth_dirs",
        VdiTornadoGraphQLHandler,
        dict(graphiql=True, schema=auth_dir_schema),
    ),
    (r"/pools", VdiTornadoGraphQLHandler, dict(graphiql=True, schema=pool_schema)),
    (r"/events", VdiTornadoGraphQLHandler, dict(graphiql=True, schema=event_schema)),
    (
        r"/settings",
        VdiTornadoGraphQLHandler,
        dict(graphiql=True, schema=settings_schema)
    ),
    (r"/tasks", VdiTornadoGraphQLHandler, dict(graphiql=True, schema=task_schema)),
    (
        r"/thin_clients",
        VdiTornadoGraphQLHandler,
        dict(graphiql=True, schema=thin_client_schema),
    ),
    (r"/statistics", VdiTornadoGraphQLHandler, dict(graphiql=True, schema=statistics_schema)),
    (r"/broker_info", VdiTornadoGraphQLHandler, dict(graphiql=True, schema=broker_info_schema)),
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
    return Application(
        handlers,
        debug=DEBUG,
        websocket_ping_interval=WS_PING_INTERVAL,
        websocket_ping_timeout=WS_PING_TIMEOUT,
        autoreload=autoreload
    )


def make_ssl():
    ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(SSL_CRT_FPATH, SSL_KEY_FPATH)
    ssl_ctx.verify_mode = ssl.CERT_OPTIONAL
    return ssl_ctx


def exit_handler(sig, frame):  # noqa
    io_loop = IOLoop.current()

    async def shutdown():
        await stop_veil_client()
        await system_logger.info(_local_("VDI broker stopped."))
        await stop_gino()
        await redis_deinit()
        io_loop.stop()

    io_loop.add_callback_from_signal(shutdown)


async def startup_alerts(vdi_license):
    """Выводим сообщения только в первом процессе. Если task_id None, значит процесс 1, если > 0, значит больше 1."""
    if not task_id():
        await system_logger.info(
            _local_("{} instance(s) of VDI broker web application launched on {}.").format(options.workers,
                                                                                           socket.gethostname())
        )
        # Проверка настроек
        if not AUTH_ENABLED:
            await system_logger.warning(_local_("Authentication system is disabled."))
        if vdi_license.expired:
            await system_logger.warning(
                _local_(
                    "The license is expired on {}. Some functions will be blocked. Contact your dealer."
                ).format(socket.gethostname())
            )
        if DEBUG:
            await system_logger.warning(_local_("DEBUG mode is enabled."))


async def init_systems():
    """Инитализация систем. Здесь код требующий асинхронного выполнерия."""
    # Инициализация БД
    await start_gino(app)

    # Инициализация лицензии
    license_obj = await License.get_license()

    # Вывод уведомлений
    await startup_alerts(license_obj)


if __name__ == "__main__":
    # Парсинг аргументов
    options.parse_command_line()

    # signals
    init_signals(exit_handler)
    app = make_app()

    # Инициализация редис
    redis_init()

    # Инициализация HTTP клиента (контроллеров)
    get_veil_client_singleton()

    # Запуск tornado
    if options.ssl:
        ssl_options = make_ssl()
        server = HTTPServer(app, ssl_options=ssl_options)
    else:
        server = HTTPServer(app)

    server.listen(port=options.port, address=options.address)
    server.start(options.workers)

    IOLoop.current().run_sync(init_systems)

    IOLoop.current().start()
