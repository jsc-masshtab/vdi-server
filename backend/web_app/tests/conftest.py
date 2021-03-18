# -*- coding: utf-8 -*-
import os

# import asyncio
import pytest  # noqa

from yarl import URL
from types import SimpleNamespace
from sqlalchemy_utils import create_database, database_exists, drop_database
from alembic.command import upgrade

# from gino_tornado import Gino

from common.settings import DB_HOST, DB_PASS, DB_PORT, DB_USER
from common.migrations.utils import make_alembic_config


@pytest.fixture(scope="session")
def pg_url():
    """Предоставляет базовый URL-адрес PostgreSQL для создания временной базы данных для тестов."""
    url = "postgresql://{USER}:{PASS}@{HOST}:{PORT}/".format(
        USER=DB_USER, PASS=DB_PASS, HOST=DB_HOST, PORT=DB_PORT
    )
    pg_url = URL(os.getenv("CI_TESTS_PG_URL", url))
    return pg_url


@pytest.fixture(scope="session", autouse=True)
def postgres(pg_url):
    """Создает временную БД для запуска теста."""
    tmp_name = "tests"
    tmp_url = str(pg_url.with_path(tmp_name))

    if database_exists(tmp_url):
        drop_database(tmp_url)
    create_database(tmp_url)

    try:
        cmd_options = SimpleNamespace(
            config="alembic.ini",
            name="migrations",
            pg_url=tmp_url,
            raiseerr=False,
            x=None,
        )
        upgrade(make_alembic_config(cmd_options), "head")
        yield tmp_url
    finally:
        drop_database(tmp_url)
        print("FINISH")


@pytest.fixture(scope="session")
def alembic_config(postgres):
    """Создает объект с конфигурацией для alembic, настроенный на временную БД."""
    cmd_options = SimpleNamespace(
        config="alembic.ini", name="migrations", pg_url=postgres, raiseerr=False, x=None
    )
    return make_alembic_config(cmd_options)


# @pytest.fixture(autouse=True)  # убрать из postgres (autouse=True)
# async def migrated_postgres(alembic_config, postgres):
#     """
#     Возвращает URL к БД с примененными миграциями.
#     """
#     upgrade(alembic_config, 'head')
#     return postgres


# def create_connection():
#     connection = None
#     try:
#         connection = psycopg2.connect(
#             database='tests',
#             user=DB_USER,
#             password=DB_PASS,
#             host=DB_HOST,
#             port=DB_PORT,
#         )
#         print("Connection to PostgreSQL DB successful")
#     except Exception as e:
#         raise e
#     return connection
#
#
# @pytest.fixture(scope="session", autouse=True)
# def db_connection(postgres):
#     connection = create_connection()


# @pytest.fixture(scope="session")
# async def init_gino(migrated_postgres):
#     from common.database import start_gino, stop_gino
#
#     db = Gino()
#
#     async def starting_gino():
#         await db.set_bind(migrated_postgres)
#
#     async def stopping_gino():
#         await db.pop_bind().close()
#
#     await stop_gino()
#     IOLoop.current().stop()
#     IOLoop.current().run_sync(lambda: starting_gino())
#     IOLoop.current().start()


# @pytest.fixture(autouse=True)
# async def db_fixture(request, migrated_postgres):
#     """Запускается перед первым тестом и завершается после последнего."""
#     import nest_asyncio
#     nest_asyncio.apply()
#
#     loop = asyncio.get_event_loop()
#     database = Gino()
#
#     async def setup():
#         from tornado.ioloop import IOLoop
#
#         async def gino_init():
#             await database.set_bind(migrated_postgres)
#
#         IOLoop.current().run_sync(lambda: gino_init())
#         IOLoop.current().start()
#     loop.run_until_complete(setup())
#
#     def teardown():
#         async def a_teardown():
#             try:
#                 await database.pop_bind().close()
#             except Exception as e:
#                 raise e
#
#         loop.run_until_complete(a_teardown())
#
#     request.addfinalizer(teardown)
#     return True
