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
        'cpu_count': None,
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
            'cpu_count': None,
            'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
            'memory_count': 4096,
            'status': 'ACTIVE',
            'verbose_name': '19_10-thin_child'
        }
    ]
}

snapshots['test_request_vms 2'] = {
    'vms': [
        {
            'controller': {
                'verbose_name': 'controller_added_during_test'
            },
            'cpu_count': None,
            'id': 'e00219af-f99a-4615-bd3c-85646be3e1d5',
            'memory_count': 4096,
            'status': 'ACTIVE',
            'verbose_name': '19_10-thin_child'
        }
    ]
}

snapshots['test_request_vms 3'] = {
    'vm': {
        'cpu_count': None,
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
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': 'bfcae970-a8a7-4bf6-85d1-7ad46ff6b71f',
            'status': 'ACTIVE',
            'verbose_name': '18_04_nv'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': '589ea6af-03b6-4224-a286-48f0e038ce12',
            'status': 'ACTIVE',
            'verbose_name': '19_10'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': '7f2d670b-98b0-49a8-8ecf-13acbe6fa886',
            'status': 'ACTIVE',
            'verbose_name': 'astra_clone_110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': '432b8b62-49e0-4738-8659-d3686fd17484',
            'status': 'ACTIVE',
            'verbose_name': 'debian'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': 'e50db715-18cb-46ee-8bf8-56f2bb0b2649',
            'status': 'ACTIVE',
            'verbose_name': 'u18_1'
        }
    ]
}

snapshots['test_request_templates 2'] = {
    'templates': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': '432b8b62-49e0-4738-8659-d3686fd17484',
            'status': 'ACTIVE',
            'verbose_name': 'debian'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': '589ea6af-03b6-4224-a286-48f0e038ce12',
            'status': 'ACTIVE',
            'verbose_name': '19_10'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': '70fb5b5a-96ba-458d-a546-1e4535710292',
            'status': 'ACTIVE',
            'verbose_name': 'ubuntu_20.04_sasha'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': '7f2d670b-98b0-49a8-8ecf-13acbe6fa886',
            'status': 'ACTIVE',
            'verbose_name': 'astra_clone_110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                'verbose_name': 'test controller'
            },
            'id': 'bfcae970-a8a7-4bf6-85d1-7ad46ff6b71f',
            'status': 'ACTIVE',
            'verbose_name': '18_04_nv'
        }
    ]
}

snapshots['test_request_templates 3'] = {
    'template': {
        'status': 'ACTIVE',
        'verbose_name': 'debian'
    }
}
