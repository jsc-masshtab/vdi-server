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
            'address': '0.0.0.0',
            'description': 'controller_added_during_test',
            'verbose_name': 'controller_added_during_test',
            'version': '4.5.0'
        }
    ]
}

snapshots['test_resolve_controller 1'] = {
    'controller': {
        'address': '0.0.0.0',
        'clusters': [],
        'data_pools': [],
        'description': 'controller_added_during_test',
        'nodes': [],
        'pools': [],
        'status': 'ACTIVE',
        'templates': [],
        'token': 'jwt eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxOTEyOTM3NjExLCJzc28iOmZhbHNlLCJvcmlnX2lhdCI6MTU5ODQ0MTYxMX0.OSRio0EoWA8ZDtvzl3YlaBmdfbI0DQz1RiGAIMCgoX0',
        'verbose_name': 'controller_added_during_test',
        'version': '4.5.0',
        'vms': []
    }
}
