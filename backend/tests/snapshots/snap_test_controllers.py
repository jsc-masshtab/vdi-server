# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_credentials 1'] = {
    'testController': {
        'ok': True
    }
}

snapshots['test_resolve_controllers 1'] = {
    'controllers': [
        {
            'address': '192.168.11.102',
            'description': None,
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'verbose_name': 'test controller',
            'version': None
        }
    ]
}
