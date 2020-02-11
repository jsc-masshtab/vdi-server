# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestGroupSchema.test_group_list 1'] = {
    'groups': [
        {
            'description': None,
            'users': [
            ],
            'verbose_name': 'test_group_1'
        }
    ]
}

snapshots['TestGroupSchema.test_group_get_by_id 1'] = {
    'group': {
        'description': None,
        'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
        'users': [
        ],
        'verbose_name': 'test_group_1'
    }
}

snapshots['TestGroupSchema.test_group_edit 1'] = {
    'updateGroup': {
        'group': {
            'users': [
            ],
            'verbose_name': 'test group updated'
        },
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_create 1'] = {
    'createGroup': {
        'group': {
            'users': [
            ],
            'verbose_name': 'test group 2'
        },
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_delete 1'] = {
    'deleteGroup': {
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_user_add 1'] = {
    'addGroupUsers': {
        'group': {
            'users': [
                {
                    'email': 'admin@admin.admin'
                }
            ],
            'verbose_name': 'test_group_1'
        },
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_user_remove 1'] = {
    'removeGroupUsers': {
        'group': {
            'users': [
            ],
            'verbose_name': 'test_group_1'
        },
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_role 1'] = {
    'addGroupRole': {
        'group': {
            'assigned_roles': [
                'NETWORK_ADMINISTRATOR',
                'VM_OPERATOR'
            ],
            'possible_roles': [
                'READ_ONLY',
                'ADMINISTRATOR',
                'SECURITY_ADMINISTRATOR',
                'VM_ADMINISTRATOR',
                'STORAGE_ADMINISTRATOR'
            ],
            'verbose_name': 'test_group_1'
        },
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_role 2'] = {
    'removeGroupRole': {
        'group': {
            'assigned_roles': [
                'NETWORK_ADMINISTRATOR'
            ],
            'possible_roles': [
                'READ_ONLY',
                'ADMINISTRATOR',
                'SECURITY_ADMINISTRATOR',
                'VM_ADMINISTRATOR',
                'STORAGE_ADMINISTRATOR',
                'VM_OPERATOR'
            ],
            'verbose_name': 'test_group_1'
        },
        'ok': True
    }
}
