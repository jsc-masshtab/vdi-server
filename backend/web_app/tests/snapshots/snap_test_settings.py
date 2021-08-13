# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_request_services 1'] = {
    'services': [
        {
            'status': 'running',
            'verbose_name': 'Сервер Apache.'
        },
        {
            'status': 'running',
            'verbose_name': 'База данных.'
        },
        {
            'status': 'running',
            'verbose_name': 'Redis.'
        },
        {
            'status': 'running',
            'verbose_name': 'Монитор состояния компонентов.'
        },
        {
            'status': 'running',
            'verbose_name': 'Обработчик задач.'
        },
        {
            'status': 'running',
            'verbose_name': 'Веб-приложение.'
        }
    ]
}
