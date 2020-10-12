# -*- coding: utf-8 -*-
import pytest

from types import SimpleNamespace

from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.script import Script, ScriptDirectory

from common.migrations.utils import make_alembic_config

from common.settings import DB_USER, DB_PASS, DB_HOST

pytestmark = [pytest.mark.migrations]


def get_revisions():
    """
    Создаем объект с конфигурацей alembic
    """
    tmp_url = 'postgresql://{USER}:{PASS}@{HOST}/tests'.format(USER=DB_USER, PASS=DB_PASS, HOST=DB_HOST)
    options = SimpleNamespace(config='alembic.ini', pg_url=tmp_url,
                              name='migrations', raiseerr=False, x=None)
    config = make_alembic_config(options)

    # Получаем директорию с миграциями alembic
    revisions_dir = ScriptDirectory.from_config(config)

    # Получаем миграции и сортируем в порядке от первой до последней
    revisions = list(revisions_dir.walk_revisions('base', 'heads'))
    revisions.reverse()
    return revisions


@pytest.mark.asyncio
@pytest.mark.parametrize('revision', get_revisions())
async def test_migrations(alembic_config: Config, revision: Script):
    if revision.down_revision:
        downgrade(alembic_config, revision.down_revision)
    else:
        downgrade(alembic_config, 'base')
    upgrade(alembic_config, revision.revision)
    # -1 используется для downgrade первой миграции (т.к. ее down_revision равен None)
    downgrade(alembic_config, revision.down_revision or '-1')
    upgrade(alembic_config, revision.revision)
