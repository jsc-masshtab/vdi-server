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
            'address': '192.168.11.115',
            'description': None,
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'verbose_name': 'test controller',
            'version': None
        }
    ]
}

snapshots['test_resolve_controller 1'] = {
    'controller': {
        'address': '192.168.11.115',
        'clusters': [
            {
                'cpu_count': 128,
                'id': '7f38868f-2c13-4c42-a08f-ade0b093d9d4',
                'memory_count': 257240,
                'nodes_count': 4,
                'status': 'ACTIVE',
                'tags': [
                ],
                'verbose_name': 'second_cluster'
            },
            {
                'cpu_count': 12,
                'id': 'c3f56e1f-9bd1-45e8-a3e6-a5f69256ee5e',
                'memory_count': 32065,
                'nodes_count': 1,
                'status': 'ACTIVE',
                'tags': [
                ],
                'verbose_name': 'cluster_115'
            },
            {
                'cpu_count': 84,
                'id': '5c8cd4ff-b42d-412e-b9b8-2fa55dcf477c',
                'memory_count': 353799,
                'nodes_count': 5,
                'status': 'ACTIVE',
                'tags': [
                    '#d20404'
                ],
                'verbose_name': 'Veil default cluster'
            },
            {
                'cpu_count': 0,
                'id': '3f8ab821-0b86-40d6-be56-7420a738ccc1',
                'memory_count': 0,
                'nodes_count': 0,
                'status': 'ACTIVE',
                'tags': [
                ],
                'verbose_name': 'Second Location default cluster'
            }
        ],
        'data_pools': [
            {
                'file_count': 3,
                'free_space': 77633,
                'hints': 0,
                'id': '1f029611-5f38-4ef0-b800-5d957024addc',
                'iso_count': 0,
                'size': 93353,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 15720,
                'vdisk_count': 0,
                'verbose_name': 'test_110'
            },
            {
                'file_count': 0,
                'free_space': 914242,
                'hints': 0,
                'id': 'c50c5685-78ef-4684-b3fe-cd5e3978b14e',
                'iso_count': 2,
                'size': 920575,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'zfs',
                'used_space': 6333,
                'vdisk_count': 0,
                'verbose_name': 'rd_zfs'
            },
            {
                'file_count': 1,
                'free_space': 868970,
                'hints': 0,
                'id': '29b17665-2a33-4db5-98a2-86d954d8d33b',
                'iso_count': 1,
                'size': 920575,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'zfs',
                'used_space': 51605,
                'vdisk_count': 4,
                'verbose_name': 'zfs_113'
            },
            {
                'file_count': 0,
                'free_space': 909904,
                'hints': 0,
                'id': '07515dc3-539b-4a5c-ae3d-3c40cb82dffb',
                'iso_count': 2,
                'size': 920575,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'zfs',
                'used_space': 10671,
                'vdisk_count': 3,
                'verbose_name': 'zfs_114'
            },
            {
                'file_count': 0,
                'free_space': 789944,
                'hints': 0,
                'id': '1da024ba-fe95-4071-b346-e91b99f90da1',
                'iso_count': 0,
                'size': 838776,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 48832,
                'vdisk_count': 1,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.9.217'
            },
            {
                'file_count': 0,
                'free_space': 775617,
                'hints': 0,
                'id': '39406aa1-de25-45bb-a525-525316830ff4',
                'iso_count': 3,
                'size': 838776,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 63159,
                'vdisk_count': 1,
                'verbose_name': 'testing'
            },
            {
                'file_count': 0,
                'free_space': 796024,
                'hints': 0,
                'id': 'c20c83a0-2a14-4387-9b5f-c667abd176dc',
                'iso_count': 0,
                'size': 838776,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 42752,
                'vdisk_count': 0,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.6.93_long_long_name'
            },
            {
                'file_count': 1,
                'free_space': 325690,
                'hints': 0,
                'id': '01531445-3dbf-4c59-997f-66902b68a8e5',
                'iso_count': 1,
                'size': 369821,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 44131,
                'vdisk_count': 3,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.11.111'
            },
            {
                'file_count': 1,
                'free_space': 793607,
                'hints': 0,
                'id': '6e35d659-28c6-460c-864e-7ca77f618746',
                'iso_count': 0,
                'size': 839783,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 46176,
                'vdisk_count': 1,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.11.114_for_virtual_veils'
            },
            {
                'file_count': 18,
                'free_space': 88454,
                'hints': 0,
                'id': 'c577b169-0293-4f5f-9ea1-c0777e502f6a',
                'iso_count': 4,
                'size': 237961,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'nfs',
                'used_space': 149507,
                'vdisk_count': 1,
                'verbose_name': 'nfs'
            },
            {
                'file_count': 1,
                'free_space': 240523,
                'hints': 0,
                'id': '806ca3df-01c1-4c99-877e-02c149453c47',
                'iso_count': 2,
                'size': 440447,
                'status': 'ACTIVE',
                'tags': [
                    '#d20404'
                ],
                'type': 'zfs',
                'used_space': 199924,
                'vdisk_count': 7,
                'verbose_name': 'zfs_110'
            },
            {
                'file_count': 0,
                'free_space': 775617,
                'hints': 0,
                'id': '1c117d5f-8c29-4563-a17c-4dc6f6f3efa1',
                'iso_count': 0,
                'size': 838776,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 63159,
                'vdisk_count': 0,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.6.171'
            },
            {
                'file_count': 0,
                'free_space': 796980,
                'hints': 0,
                'id': '26c6b271-7cf9-4a55-8c4e-38f28a2a9c62',
                'iso_count': 0,
                'size': 839783,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 42803,
                'vdisk_count': 1,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.11.112'
            },
            {
                'file_count': 12,
                'free_space': 135564,
                'hints': 1,
                'id': '69f1cc26-c0e8-4406-a378-9d7b3e553898',
                'iso_count': 14,
                'size': 839783,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 704219,
                'vdisk_count': 19,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.11.110'
            },
            {
                'file_count': 0,
                'free_space': 796024,
                'hints': 0,
                'id': 'ef990d37-b1d6-4ab6-9d75-20562054a441',
                'iso_count': 0,
                'size': 838776,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 42752,
                'vdisk_count': 0,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.6.110'
            },
            {
                'file_count': 27,
                'free_space': 434185,
                'hints': 0,
                'id': '1253e6ed-60c1-4337-9e72-c0955358d429',
                'iso_count': 5,
                'size': 905477,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 471292,
                'vdisk_count': 20,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.11.115'
            },
            {
                'file_count': 1,
                'free_space': 755054,
                'hints': 0,
                'id': 'a373bbb1-eef5-4701-99b1-1599a26b1e0a',
                'iso_count': 1,
                'size': 839783,
                'status': 'ACTIVE',
                'tags': [
                ],
                'type': 'local',
                'used_space': 84729,
                'vdisk_count': 4,
                'verbose_name': 'Базовый локальный пул данных узла 192.168.11.113'
            }
        ],
        'description': None,
        'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
        'nodes': [
            {
                'cpu_count': '24',
                'id': '39d23118-d37a-454d-a74d-899d1bf2065f',
                'management_ip': '192.168.11.111',
                'memory_count': '32021',
                'status': 'ACTIVE',
                'verbose_name': '192.168.11.111'
            },
            {
                'cpu_count': '32',
                'id': '8f5a05c1-be0e-47a3-ab90-b3cdce49ac33',
                'management_ip': '192.168.9.217',
                'memory_count': '64310',
                'status': 'ACTIVE',
                'verbose_name': '192.168.9.217'
            },
            {
                'cpu_count': '12',
                'id': '7b9bc3fa-d6bc-4dde-9de1-c3875cc267a8',
                'management_ip': '192.168.11.113',
                'memory_count': '32058',
                'status': 'ACTIVE',
                'verbose_name': '192.168.11.113'
            },
            {
                'cpu_count': '24',
                'id': '85e68238-8bf6-4f5b-a06c-1926f38df05b',
                'management_ip': '192.168.11.110',
                'memory_count': '128830',
                'status': 'ACTIVE',
                'verbose_name': '192.168.11.110'
            },
            {
                'cpu_count': '12',
                'id': '31e58f10-fbf1-45b1-a140-414329481fce',
                'management_ip': '192.168.11.114',
                'memory_count': '128832',
                'status': 'ACTIVE',
                'verbose_name': '192.168.11.114_for_virtual_veils'
            },
            {
                'cpu_count': '12',
                'id': '36b254da-1304-4c68-b1e8-55edc8fe927e',
                'management_ip': '192.168.11.112',
                'memory_count': '32058',
                'status': 'ACTIVE',
                'verbose_name': '192.168.11.112'
            },
            {
                'cpu_count': '32',
                'id': '45d948c1-44e9-4860-9f1f-640a0f69bd3b',
                'management_ip': '192.168.6.93',
                'memory_count': '64310',
                'status': 'ACTIVE',
                'verbose_name': '192.168.6.93_long_long_name'
            },
            {
                'cpu_count': '32',
                'id': 'a6b7cb9f-6ee6-497f-b8f6-74243b3fc90a',
                'management_ip': '192.168.6.110',
                'memory_count': '64310',
                'status': 'ACTIVE',
                'verbose_name': '192.168.6.110'
            },
            {
                'cpu_count': '32',
                'id': '6e82c8b8-64a7-4ec7-aebc-737ecc497030',
                'management_ip': '192.168.6.171',
                'memory_count': '64310',
                'status': 'ACTIVE',
                'verbose_name': '192.168.6.171'
            },
            {
                'cpu_count': '12',
                'id': 'cdf10fc6-57f8-436c-a031-78ba3ba1ae40',
                'management_ip': '192.168.11.115',
                'memory_count': '32065',
                'status': 'ACTIVE',
                'verbose_name': '192.168.11.115'
            }
        ],
        'pools': [
        ],
        'status': 'ACTIVE',
        'templates': [
            {
                'id': '432b8b62-49e0-4738-8659-d3686fd17484',
                'verbose_name': 'debian'
            },
            {
                'id': '589ea6af-03b6-4224-a286-48f0e038ce12',
                'verbose_name': '19_10'
            },
            {
                'id': '70fb5b5a-96ba-458d-a546-1e4535710292',
                'verbose_name': 'ubuntu_20.04_sasha'
            },
            {
                'id': '7f2d670b-98b0-49a8-8ecf-13acbe6fa886',
                'verbose_name': 'astra_clone_110'
            },
            {
                'id': 'bfcae970-a8a7-4bf6-85d1-7ad46ff6b71f',
                'verbose_name': '18_04_nv'
            },
            {
                'id': 'c94b202c-1d4e-4ccb-a6b9-de761cf17834',
                'verbose_name': 'win10_demo_1'
            },
            {
                'id': 'e50db715-18cb-46ee-8bf8-56f2bb0b2649',
                'verbose_name': 'u18_1'
            },
            {
                'id': 'ed8af737-7518-49ac-bbe5-7109956dff77',
                'verbose_name': 'vm_win10_d.gubin'
            },
            {
                'id': 'ee9884f9-3f96-4ce6-8ab2-6425b8b93307',
                'verbose_name': 'veil_node'
            }
        ],
        'token': 'jwt eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxNjUsInVzZXJuYW1lIjoiYXBpLWNsaSIsImV4cCI6MTkwODI2MjI1Niwic3NvIjpmYWxzZSwib3JpZ19pYXQiOjE1OTM3NjYyNTZ9._41CVXezP1vDHoZyQ71UcadqPdti7-tmy_teEjfBgio',
        'verbose_name': 'test controller',
        'version': None,
        'vms': [
            {
                'id': '06bb682f-672a-40ef-aff8-cb43dfe9d4f2',
                'verbose_name': 'veil_node-thin_child'
            },
            {
                'id': '09c1daaf-66e9-47bd-ac94-9d1bf454df5a',
                'verbose_name': 'astra2345'
            },
            {
                'id': '13d8f8ca-67c1-4fa3-b2a9-01e397cd6472',
                'verbose_name': 'alt_9'
            },
            {
                'id': '1554b412-92ff-4b0a-a814-275a84ee3891',
                'verbose_name': 'test_2'
            },
            {
                'id': '205e8002-42c0-4bce-b5a2-07897cd41c0d',
                'verbose_name': 'Ubuntu_qxl'
            },
            {
                'id': '22c22283-b047-4bd8-8e93-e167f47bbe17',
                'verbose_name': 'aster'
            },
            {
                'id': '2872b76a-601d-4f55-939f-3cfd750cc20c',
                'verbose_name': 'win10_komdiv'
            },
            {
                'id': '2d7ead38-a920-4c1a-855b-3fefa3760f95',
                'verbose_name': 'ubuntu_19.10_node_114'
            },
            {
                'id': '32692599-5108-4f88-9493-067f1c936a17',
                'verbose_name': 'win10_demo01'
            },
            {
                'id': '33eff414-2d5e-49a2-8891-cea391ac8eb9',
                'verbose_name': 'vdi-test-install'
            },
            {
                'id': '36d599d7-ee0d-480a-a2a8-661412f04aab',
                'verbose_name': 'win10_demo'
            },
            {
                'id': '4006bb0a-70c5-47e3-ba30-c8d2b583c256',
                'verbose_name': 'xubuntu_gubin_1-2'
            },
            {
                'id': '4648fa1d-a593-48fd-8619-93f51341b234',
                'verbose_name': 'rd_bm'
            },
            {
                'id': '482870ce-80c4-4064-876d-8ea9aac85fe7',
                'verbose_name': 'win10_demo02'
            },
            {
                'id': '484721b7-42b6-4ef3-a941-9cf43cef591a',
                'verbose_name': 'win10_demo-oleg'
            },
            {
                'id': '5b15f03c-d007-4877-8266-a92ea8fc88e8',
                'verbose_name': 'NovaVM2'
            },
            {
                'id': '5b3aef1c-c444-4ff0-83b0-d368cbc70a95',
                'verbose_name': 'zabbix-5.0'
            },
            {
                'id': '5bc4dc96-4cde-4877-be21-8860319e4839',
                'verbose_name': 'alt_ws_9'
            },
            {
                'id': '6b8240d4-48b6-412a-ac90-dac2b829ff8f',
                'verbose_name': 'NovaVM'
            },
            {
                'id': '82a5a14b-a652-4f89-b51c-3e44c81fe74e',
                'verbose_name': 'RDSH_3D'
            },
            {
                'id': '88d18967-d1cc-4238-ae2c-5e9d042dafed',
                'verbose_name': 'debian_test'
            },
            {
                'id': '8a05558f-1a67-4bcc-b9cf-215de7167347',
                'verbose_name': 'win10_moiseev'
            },
            {
                'id': '8b8644b8-4c0f-49d3-9b16-9408af4abb55',
                'verbose_name': 'Ubuntu_NX'
            },
            {
                'id': '907e3335-4f6b-4de9-a9ef-be0253befb71',
                'verbose_name': 'NLS'
            },
            {
                'id': '93267eba-fba5-42c0-a645-49009bda4c36',
                'verbose_name': 'win2k16'
            },
            {
                'id': 'a078a56b-e0d0-4ea5-bd76-721b045c9580',
                'verbose_name': 'xubuntu_2004_node_110-clone'
            },
            {
                'id': 'a2642e55-7697-4c8f-9d9b-f8a24e02511b',
                'verbose_name': 'test_aster'
            },
            {
                'id': 'a72c67e1-13fa-46b8-a0a9-7442ed4136f5',
                'verbose_name': 'aster_clone'
            },
            {
                'id': 'ac931ffe-4346-4bb3-897b-43d89ce68914',
                'verbose_name': 'astra'
            },
            {
                'id': 'b929a509-b3f0-46b4-8d5a-997e05c4f550',
                'verbose_name': 'ubuntu_19.10'
            },
            {
                'id': 'b9ce563f-9808-4406-8071-dae0b19017c4',
                'verbose_name': 'proxmox'
            },
            {
                'id': 'ba1e6d7b-54ff-4ca4-9d92-0010475d1aad',
                'verbose_name': 'vdi-gogolev'
            },
            {
                'id': 'be1ae32b-b10e-460c-a73d-88c97aa685f2',
                'verbose_name': 'win10_solomin'
            },
            {
                'id': 'c127419c-72ad-4673-864a-d32ac4a00a4e',
                'verbose_name': 'xubuntu_2004_node_110'
            },
            {
                'id': 'c2fb06c2-272b-4524-b28b-6ca6b408e8cb',
                'verbose_name': 'debian_buster'
            },
            {
                'id': 'ccd98c60-53dd-4f06-8b3a-f2338fb8406d',
                'verbose_name': 'test_helper'
            },
            {
                'id': 'cf7fd0aa-37db-439d-b661-ff08ec456a20',
                'verbose_name': 'ss'
            },
            {
                'id': 'd5c27c23-36f7-4dee-8328-06e408788d3a',
                'verbose_name': 'win7'
            },
            {
                'id': 'd6b9aa9d-b0fb-4c7a-8580-457d2850e72f',
                'verbose_name': 'nls_copy'
            },
            {
                'id': 'eee8dc66-7139-4cd2-8df5-966be5bfaab0',
                'verbose_name': 'vdi-server-2.0.2-moiseev'
            },
            {
                'id': 'f64309c2-1757-4b7c-8d49-d24343548344',
                'verbose_name': 'vdi-server-old_1'
            },
            {
                'id': 'f83ccb2f-8fe9-454a-89c9-473164138f20',
                'verbose_name': 'vm1-on-ctrl-120'
            }
        ]
    }
}
