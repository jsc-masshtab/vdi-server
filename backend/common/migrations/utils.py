# -*- coding: utf-8 -*-
import os

from alembic.config import Config
from types import SimpleNamespace

path = os.path.dirname(__file__)


def make_alembic_config(cmd_opts: SimpleNamespace, base_path: str = path) -> Config:
    """
    Создает объект конфигурации alembic на основе аргументов командной строки
    """
    # путь до файла alembic.ini
    cmd_opts.config = os.path.join(base_path, cmd_opts.config)

    config = Config(file_=cmd_opts.config, ini_section=cmd_opts.name, cmd_opts=cmd_opts)

    # путь до папки с alembic
    config.set_main_option("script_location", base_path)
    if cmd_opts.pg_url:
        config.set_main_option("sqlalchemy.url", cmd_opts.pg_url)

    return config
