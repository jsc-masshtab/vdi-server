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

snapshots['test_update_automated_pool 1'] = {
    'pool': {
        'increase_step': 2,
        'keep_vms_on': True,
        'pool_type': 'AUTOMATED',
        'reserve_size': 1,
        'status': 'ACTIVE',
        'total_size': 4,
        'vm_action_upon_user_disconnect': 'SHUTDOWN',
        'vm_disconnect_action_timeout': 55
    }
}

snapshots['test_update_static_pool 1'] = {
    'pool': {
        'keep_vms_on': True,
        'pool_type': 'STATIC',
        'status': 'ACTIVE',
        'vm_action_upon_user_disconnect': 'NONE',
        'vm_disconnect_action_timeout': 55
    }
}
