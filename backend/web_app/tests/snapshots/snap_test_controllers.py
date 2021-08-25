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

snapshots['test_resolve_controller 1'] = {
    'controller': {
        'address': '0.0.0.0',
        'clusters': [
            {
                'cpu_count': 12,
                'id': 'c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e',
                'memory_count': 32065,
                'nodes_count': 1,
                'status': 'ACTIVE',
                'tags': [
                ],
                'verbose_name': 'cluster_115'
            }
        ],
        'data_pools': [
            {
                'file_count': 0,
                'free_space': 3402402,
                'hints': 2,
                'id': 'ba13e5a5-d405-4ea3-bb74-82c139a0638a',
                'iso_count': 0,
                'size': 3603492,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'nfs',
                'used_space': 201090,
                'vdisk_count': 1,
                'verbose_name': 'trans'
            }
        ],
        'description': 'controller_added_during_test',
        'nodes': [
            {
                'cpu_count': '24',
                'id': '39d23118-d37a-454d-a74d-899d1bf2065f',
                'management_ip': '192.168.11.111',
                'memory_count': '32021',
                'status': 'ACTIVE',
                'verbose_name': '192.168.11.111'
            }
        ],
        'pools': [
        ],
        'resource_pools': [
        ],
        'status': 'ACTIVE',
        'templates': [
            {
                'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
                'verbose_name': '19_10-thin_child-1'
            }
        ],
        'token': '************',
        'veil_events': [
            {
                'id': '9863da03-5497-4df1-947e-0ce360631062'
            }
        ],
        'veil_events_count': 1,
        'verbose_name': 'controller_added_during_test',
        'version': '4.6.0',
        'vms': [
            {
                'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
                'verbose_name': '19_10-thin_child-1'
            }
        ]
    }
}

snapshots['test_resolve_controllers 1'] = {
    'controllers': [
        {
            'address': '0.0.0.0',
            'description': 'controller_added_during_test',
            'verbose_name': 'controller_added_during_test',
            'version': '4.6.0'
        }
    ]
}
