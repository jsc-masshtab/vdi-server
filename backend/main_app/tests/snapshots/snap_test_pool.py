# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestPoolPermissionsSchema.test_pool_user_permission 1'] = {
    'entitleUsersToPool': {
        'ok': True,
        'pool': {
            'users': [
                {
                    'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
                },
                {
                    'id': 'f9599771-cc95-45e4-9ae5-c8177b796aff'
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
                    'id': 'f9599771-cc95-45e4-9ae5-c8177b796aff'
                }
            ]
        }
    }
}

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

snapshots['TestPoolPermissionsSchema.test_pool_role_permission 1'] = {
    'addPoolRole': {
        'ok': True,
        'pool': {
            'assigned_roles': [
                'READ_ONLY',
                'VM_ADMINISTRATOR'
            ],
            'possible_roles': [
                'READ_ONLY',
                'ADMINISTRATOR',
                'SECURITY_ADMINISTRATOR',
                'VM_ADMINISTRATOR',
                'NETWORK_ADMINISTRATOR',
                'STORAGE_ADMINISTRATOR',
                'VM_OPERATOR'
            ]
        }
    }
}

snapshots['TestPoolPermissionsSchema.test_pool_role_permission 2'] = {
    'removePoolRole': {
        'ok': True,
        'pool': {
            'assigned_roles': [
                'VM_ADMINISTRATOR'
            ],
            'possible_roles': [
                'READ_ONLY',
                'ADMINISTRATOR',
                'SECURITY_ADMINISTRATOR',
                'VM_ADMINISTRATOR',
                'NETWORK_ADMINISTRATOR',
                'STORAGE_ADMINISTRATOR',
                'VM_OPERATOR'
            ]
        }
    }
}
