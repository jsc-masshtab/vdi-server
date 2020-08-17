# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_request_clusters 1'] = {
    'clusters': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e',
            'nodes_count': 1,
            'verbose_name': 'cluster_115'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '7f38868f-2c13-4c42-a08f-ade0b093d9d4',
            'nodes_count': 4,
            'verbose_name': 'second_cluster'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '3f8ab821-0b86-40d6-be56-7420a738ccc1',
            'nodes_count': 0,
            'verbose_name': 'Second Location default cluster'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '5c8cd4ff-b42d-412e-b9b8-2fa55dcf477c',
            'nodes_count': 5,
            'verbose_name': 'Veil default cluster'
        }
    ]
}

snapshots['test_request_clusters 2'] = {
    'clusters': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '7f38868f-2c13-4c42-a08f-ade0b093d9d4',
            'nodes_count': 4,
            'verbose_name': 'second_cluster'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '5c8cd4ff-b42d-412e-b9b8-2fa55dcf477c',
            'nodes_count': 5,
            'verbose_name': 'Veil default cluster'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e',
            'nodes_count': 1,
            'verbose_name': 'cluster_115'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '3f8ab821-0b86-40d6-be56-7420a738ccc1',
            'nodes_count': 0,
            'verbose_name': 'Second Location default cluster'
        }
    ]
}

snapshots['test_request_clusters 3'] = {
    'cluster': {
        'verbose_name': 'second_cluster'
    }
}

snapshots['test_request_nodes 1'] = {
    'nodes': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 24,
            'id': '85e68238-8bf6-4f5b-a06c-1926f38df05b',
            'verbose_name': '192.168.11.110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 24,
            'id': '39d23118-d37a-454d-a74d-899d1bf2065f',
            'verbose_name': '192.168.11.111'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': '36b254da-1304-4c68-b1e8-55edc8fe927e',
            'verbose_name': '192.168.11.112'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': '7b9bc3fa-d6bc-4dde-9de1-c3875cc267a8',
            'verbose_name': '192.168.11.113'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': '31e58f10-fbf1-45b1-a140-414329481fce',
            'verbose_name': '192.168.11.114_for_virtual_veils'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': 'cdf10fc6-57f8-436c-a031-78ba3ba1ae40',
            'verbose_name': '192.168.11.115'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 32,
            'id': 'a6b7cb9f-6ee6-497f-b8f6-74243b3fc90a',
            'verbose_name': '192.168.6.110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 32,
            'id': '6e82c8b8-64a7-4ec7-aebc-737ecc497030',
            'verbose_name': '192.168.6.171'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 32,
            'id': '45d948c1-44e9-4860-9f1f-640a0f69bd3b',
            'verbose_name': '192.168.6.93_long_long_name'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 32,
            'id': '8f5a05c1-be0e-47a3-ab90-b3cdce49ac33',
            'verbose_name': '192.168.9.217'
        }
    ]
}

snapshots['test_request_nodes 2'] = {
    'nodes': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 32,
            'id': '8f5a05c1-be0e-47a3-ab90-b3cdce49ac33',
            'verbose_name': '192.168.9.217'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 32,
            'id': '45d948c1-44e9-4860-9f1f-640a0f69bd3b',
            'verbose_name': '192.168.6.93_long_long_name'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 32,
            'id': 'a6b7cb9f-6ee6-497f-b8f6-74243b3fc90a',
            'verbose_name': '192.168.6.110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 32,
            'id': '6e82c8b8-64a7-4ec7-aebc-737ecc497030',
            'verbose_name': '192.168.6.171'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 24,
            'id': '39d23118-d37a-454d-a74d-899d1bf2065f',
            'verbose_name': '192.168.11.111'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 24,
            'id': '85e68238-8bf6-4f5b-a06c-1926f38df05b',
            'verbose_name': '192.168.11.110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': '7b9bc3fa-d6bc-4dde-9de1-c3875cc267a8',
            'verbose_name': '192.168.11.113'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': '31e58f10-fbf1-45b1-a140-414329481fce',
            'verbose_name': '192.168.11.114_for_virtual_veils'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': '36b254da-1304-4c68-b1e8-55edc8fe927e',
            'verbose_name': '192.168.11.112'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': 'cdf10fc6-57f8-436c-a031-78ba3ba1ae40',
            'verbose_name': '192.168.11.115'
        }
    ]
}

snapshots['test_request_nodes 3'] = {
    'node': {
        'cpu_count': None,
        'management_ip': '192.168.9.217',
        'memory_count': 64310,
        'status': 'ACTIVE',
        'verbose_name': '192.168.9.217'
    }
}

snapshots['test_request_datapools 1'] = {
    'datapools': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'c577b169-0293-4f5f-9ea1-c0777e502f6a',
            'verbose_name': 'nfs'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'c50c5685-78ef-4684-b3fe-cd5e3978b14e',
            'verbose_name': 'rd_zfs'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '1f029611-5f38-4ef0-b800-5d957024addc',
            'verbose_name': 'test_110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '39406aa1-de25-45bb-a525-525316830ff4',
            'verbose_name': 'testing'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '806ca3df-01c1-4c99-877e-02c149453c47',
            'verbose_name': 'zfs_110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '29b17665-2a33-4db5-98a2-86d954d8d33b',
            'verbose_name': 'zfs_113'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '07515dc3-539b-4a5c-ae3d-3c40cb82dffb',
            'verbose_name': 'zfs_114'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '69f1cc26-c0e8-4406-a378-9d7b3e553898',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '01531445-3dbf-4c59-997f-66902b68a8e5',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.111'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '26c6b271-7cf9-4a55-8c4e-38f28a2a9c62',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.112'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'a373bbb1-eef5-4701-99b1-1599a26b1e0a',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.113'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '6e35d659-28c6-460c-864e-7ca77f618746',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.114_for_virtual_veils'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '1253e6ed-60c1-4337-9e72-c0955358d429',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.115'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'ef990d37-b1d6-4ab6-9d75-20562054a441',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.6.110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '1c117d5f-8c29-4563-a17c-4dc6f6f3efa1',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.6.171'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'c20c83a0-2a14-4387-9b5f-c667abd176dc',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.6.93_long_long_name'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '1da024ba-fe95-4071-b346-e91b99f90da1',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.9.217'
        }
    ]
}

snapshots['test_request_datapools 2'] = {
    'datapools': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '806ca3df-01c1-4c99-877e-02c149453c47',
            'verbose_name': 'zfs_110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'c50c5685-78ef-4684-b3fe-cd5e3978b14e',
            'verbose_name': 'rd_zfs'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '07515dc3-539b-4a5c-ae3d-3c40cb82dffb',
            'verbose_name': 'zfs_114'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '29b17665-2a33-4db5-98a2-86d954d8d33b',
            'verbose_name': 'zfs_113'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'c577b169-0293-4f5f-9ea1-c0777e502f6a',
            'verbose_name': 'nfs'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '1f029611-5f38-4ef0-b800-5d957024addc',
            'verbose_name': 'test_110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '01531445-3dbf-4c59-997f-66902b68a8e5',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.111'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '69f1cc26-c0e8-4406-a378-9d7b3e553898',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '1c117d5f-8c29-4563-a17c-4dc6f6f3efa1',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.6.171'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '26c6b271-7cf9-4a55-8c4e-38f28a2a9c62',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.112'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'ef990d37-b1d6-4ab6-9d75-20562054a441',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.6.110'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '1253e6ed-60c1-4337-9e72-c0955358d429',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.115'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'a373bbb1-eef5-4701-99b1-1599a26b1e0a',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.113'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '1da024ba-fe95-4071-b346-e91b99f90da1',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.9.217'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '39406aa1-de25-45bb-a525-525316830ff4',
            'verbose_name': 'testing'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': 'c20c83a0-2a14-4387-9b5f-c667abd176dc',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.6.93_long_long_name'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'id': '6e35d659-28c6-460c-864e-7ca77f618746',
            'verbose_name': 'Базовый локальный пул данных узла 192.168.11.114_for_virtual_veils'
        }
    ]
}

snapshots['test_request_datapools 3'] = {
    'datapool': {
        'free_space': 240523,
        'size': 440447,
        'status': 'ACTIVE',
        'type': 'zfs',
        'verbose_name': 'zfs_110'
    }
}

snapshots['test_request_vms 1'] = {
    'vms': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 2,
            'id': '13d8f8ca-67c1-4fa3-b2a9-01e397cd6472',
            'memory_count': 4000,
            'status': 'ACTIVE',
            'verbose_name': 'alt_9'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 4,
            'id': '5bc4dc96-4cde-4877-be21-8860319e4839',
            'memory_count': 2048,
            'status': 'ACTIVE',
            'verbose_name': 'alt_ws_9'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 4,
            'id': '22c22283-b047-4bd8-8e93-e167f47bbe17',
            'memory_count': 4096,
            'status': 'ACTIVE',
            'verbose_name': 'aster'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 2,
            'id': 'a72c67e1-13fa-46b8-a0a9-7442ed4136f5',
            'memory_count': 4096,
            'status': 'ACTIVE',
            'verbose_name': 'aster_clone'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 2,
            'id': 'ac931ffe-4346-4bb3-897b-43d89ce68914',
            'memory_count': 2000,
            'status': 'ACTIVE',
            'verbose_name': 'astra'
        }
    ]
}

snapshots['test_request_vms 2'] = {
    'vms': [
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 12,
            'id': '06bb682f-672a-40ef-aff8-cb43dfe9d4f2',
            'memory_count': 6000,
            'status': 'ACTIVE',
            'verbose_name': 'veil_node-thin_child'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 1,
            'id': '09c1daaf-66e9-47bd-ac94-9d1bf454df5a',
            'memory_count': 512,
            'status': 'ACTIVE',
            'verbose_name': 'astra2345'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 2,
            'id': '13d8f8ca-67c1-4fa3-b2a9-01e397cd6472',
            'memory_count': 4000,
            'status': 'ACTIVE',
            'verbose_name': 'alt_9'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 1,
            'id': '1554b412-92ff-4b0a-a814-275a84ee3891',
            'memory_count': 512,
            'status': 'ACTIVE',
            'verbose_name': 'test_2'
        },
        {
            'controller': {
                'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
            },
            'cpu_count': 2,
            'id': '205e8002-42c0-4bce-b5a2-07897cd41c0d',
            'memory_count': 2000,
            'status': 'ACTIVE',
            'verbose_name': 'Ubuntu_qxl'
        }
    ]
}

snapshots['test_request_vms 3'] = {
    'vm': {
        'cpu_count': None,
        'id': '06bb682f-672a-40ef-aff8-cb43dfe9d4f2',
        'memory_count': 6000,
        'status': 'ACTIVE',
        'verbose_name': 'veil_node-thin_child'
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
