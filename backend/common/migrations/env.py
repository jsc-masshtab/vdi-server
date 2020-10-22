from __future__ import with_statement
from alembic import context
from sqlalchemy import pool, engine_from_config
from logging.config import fileConfig

from common.database import db as target_metadata
from common.settings import DB_USER, DB_PASS, DB_NAME, DB_HOST
from web_app.app import make_app


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
main_option = config.get_main_option('sqlalchemy.url')

# Если не тестовая БД, то формат из settings
if main_option is None or main_option.upper().find('TESTS') == -1:
    alchemy_url = 'postgres://{USER}:{PASS}@{HOST}/{NAME}'.format(USER=DB_USER, PASS=DB_PASS, HOST=DB_HOST,
                                                                  NAME=DB_NAME)
    config.set_main_option('sqlalchemy.url', alchemy_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

app = make_app()


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
