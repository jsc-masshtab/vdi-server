# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_request_services 1'] = {
    'services': [
        {
            'status': 'running',
            'verbose_name': 'Apache server'
        },
        {
            'status': 'running',
            'verbose_name': 'Database'
        },
        {
            'status': 'running',
            'verbose_name': 'Redis'
        },
        {
            'status': 'running',
            'verbose_name': 'Monitor worker'
        },
        {
            'status': 'running',
            'verbose_name': 'Task worker'
        },
        {
            'status': 'running',
            'verbose_name': 'Web application'
        }
    ]
}
