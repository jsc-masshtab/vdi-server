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
        'description': 'controller_added_during_test',
        'pools': [],
        'status': 'ACTIVE',
        'token': '*' * 12,
        'verbose_name': 'controller_added_during_test',
        'version': '4.5.0',
        'clusters': [{'id': 'c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e',
                      'verbose_name': 'cluster_115',
                      'nodes_count': 1,
                      'status': 'ACTIVE',
                      'cpu_count': 12,
                      'memory_count': 32065,
                      'tags': []}],
        'nodes': [{'id': '39d23118-d37a-454d-a74d-899d1bf2065f',
                   'verbose_name': '192.168.11.111',
                   'status': 'ACTIVE',
                   'cpu_count': '24',
                   'memory_count': '32021',
                   'management_ip': '192.168.11.111'}],
        'data_pools': [{'id': 'ba13e5a5-d405-4ea3-bb74-82c139a0638a',
                        'verbose_name': 'trans',
                        'used_space': 201090,
                        'free_space': 3402402,
                        'size': 3603492,
                        'status': 'ACTIVE',
                        'type': 'nfs',
                        'vdisk_count': 1,
                        'tags': [],
                        'hints': 2,
                        'file_count': 0,
                        'iso_count': 0}],
        'vms': [{'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5', 'verbose_name': '19_10-thin_child'}],
        'templates': [{'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5', 'verbose_name': '19_10-thin_child'}],

    }
}
