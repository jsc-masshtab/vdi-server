# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestPoolPermissionsSchema.test_pool_group_permission 1'] = {
    'addPoolGroup': {
        'ok': True,
        'pool': {
            'assigned_groups': [
                {
                    'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
                }
            ],
            'possible_groups': [
            ]
        }
    }
}

snapshots['TestPoolPermissionsSchema.test_pool_group_permission 2'] = {
    'removePoolGroup': {
        'ok': True,
        'pool': {
            'assigned_groups': [
            ],
            'possible_groups': [
                {
                    'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
                }
            ]
        }
    }
}

snapshots['TestPoolPermissionsSchema.test_pool_user_permission 1'] = {
    'entitleUsersToPool': {
        'ok': True,
        'pool': {
            'users': [
                {
                    'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
                },
                {
                    'id': 'f9599771-cc95-45e5-9ae5-c8177b796aff'
                }
            ]
        }
    }
}

snapshots['TestPoolPermissionsSchema.test_pool_user_permission 2'] = {
    'removeUserEntitlementsFromPool': {
        'ok': True,
        'pool': {
            'users': [
                {
                    'id': 'f9599771-cc95-45e5-9ae5-c8177b796aff'
                }
            ]
        }
    }
}

snapshots['test_copy_automated_pool 1'] = {
    'copyDynamicPool': {
        'pool_settings': '{"tag": null, "waiting_time": null, "keep_vms_on": false, "include_vms_in_ad": false, "max_amount_of_create_attempts": 15, "os_type": "Linux", "resource_pool_id": "5a55eee9-4687-48b4-9002-b218eefe29e3", "increase_step": 1, "controller": "7a7f97a0-4dd5-443c-8620-1bd30e12ba31", "set_vms_hostnames": false, "total_size": 2, "verbose_name": "test-pool-349abce", "is_guest": false, "ad_ou": null, "start_vms": true, "id": "87915588-ffde-4958-a837-02bf7153d7d2", "template_id": "a04ed49b-ea26-4660-8112-833a6b51d0e1", "datapool_id": "37df3326-55b9-4af1-91b3-e54df12f24e7", "status": "ACTIVE", "enable_vms_remote_access": true, "initial_size": 1, "connection_types": ["SPICE", "RDP"], "pool_type": "AUTOMATED", "vm_name_template": "vdi-test", "create_thin_clones": true, "reserve_size": 1}'
    }
}
