# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_request_clusters 1'] = {
    'clusters': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'id': 'c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e',
            'nodes_count': 1,
            'verbose_name': 'cluster_115'
        }
    ]
}

snapshots['test_request_clusters 2'] = {
    'clusters': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'id': 'c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e',
            'nodes_count': 1,
            'verbose_name': 'cluster_115'
        }
    ]
}

snapshots['test_request_clusters 3'] = {
    'cluster': {
        'verbose_name': 'cluster_115'
    }
}

snapshots['test_request_nodes 1'] = {
    'nodes': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'cpu_count': 24,
            'id': '39d23118-d37a-454d-a74d-899d1bf2065f',
            'verbose_name': '192.168.11.111'
        }
    ]
}

snapshots['test_request_nodes 2'] = {
    'nodes': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'cpu_count': 24,
            'id': '39d23118-d37a-454d-a74d-899d1bf2065f',
            'verbose_name': '192.168.11.111'
        }
    ]
}

snapshots['test_request_nodes 3'] = {
    'node': {
        'cpu_count': 24,
        'management_ip': '192.168.11.111',
        'memory_count': 32021,
        'status': 'ACTIVE',
        'verbose_name': '192.168.11.111'
    }
}

snapshots['test_request_datapools 1'] = {
    'datapools': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'id': 'ba13e5a5-d405-4ea3-bb74-82c139a0638a',
            'verbose_name': 'trans'
        }
    ]
}

snapshots['test_request_datapools 2'] = {
    'datapools': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'id': 'ba13e5a5-d405-4ea3-bb74-82c139a0638a',
            'verbose_name': 'trans'
        }
    ]
}

snapshots['test_request_datapools 3'] = {
    'datapool': {
        'free_space': 3402402,
        'size': 3603492,
        'status': 'ACTIVE',
        'type': 'local',
        'verbose_name': 'trans'
    }
}

snapshots['test_request_vms 1'] = {
    'vms': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'cpu_count': 1,
            'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
            'memory_count': 4096,
            'status': 'ACTIVE',
            'verbose_name': '19_10-thin_child-1'
        }
    ]
}

snapshots['test_request_vms 2'] = {
    'vms': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'cpu_count': 1,
            'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
            'memory_count': 4096,
            'status': 'ACTIVE',
            'verbose_name': '19_10-thin_child-1'
        }
    ]
}

snapshots['test_request_vms 3'] = {
    'vm': {
        'cpu_count': 2,
        'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
        'memory_count': 2000,
        'status': 'ACTIVE',
        'verbose_name': 'alt_linux'
    }
}

snapshots['test_request_templates 1'] = {
    'templates': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
            'status': 'ACTIVE',
            'verbose_name': '19_10-thin_child-1'
        }
    ]
}

snapshots['test_request_templates 2'] = {
    'templates': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
            'status': 'ACTIVE',
            'verbose_name': '19_10-thin_child-1'
        }
    ]
}

snapshots['test_request_templates 3'] = {
    'template': {
        'status': 'ACTIVE',
        'verbose_name': 'alt_linux'
    }
}
