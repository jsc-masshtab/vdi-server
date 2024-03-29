# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestGroupSchema.test_group_create 1'] = {
    'createGroup': {
        'group': {
            'assigned_users': [
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

snapshots['TestGroupSchema.test_group_delete_by_guid 1'] = {
    'deleteGroup': {
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_edit 1'] = {
    'updateGroup': {
        'group': {
            'assigned_users': [
            ],
            'verbose_name': 'test group updated'
        },
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_get_by_id 1'] = {
    'group': {
        'assigned_users': [
        ],
        'assigned_users_count': 0,
        'description': None,
        'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
        'possible_users': [
            {
                'email': None,
                'username': 'vdiadmin'
            }
        ],
        'possible_users_count': 1,
        'verbose_name': 'test_group_1'
    }
}

snapshots['TestGroupSchema.test_group_list 1'] = {
    'groups': [
        {
            'assigned_users': [
            ],
            'description': None,
            'possible_users': [
                {
                    'email': None,
                    'username': 'vdiadmin'
                }
            ],
            'verbose_name': 'test_group_1'
        }
    ]
}

snapshots['TestGroupSchema.test_group_role 1'] = {
    'addGroupRole': {
        'group': {
            'assigned_roles': [
                'ADMINISTRATOR',
                'OPERATOR'
            ],
            'possible_roles': [
                'SECURITY_ADMINISTRATOR'
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
                'ADMINISTRATOR'
            ],
            'possible_roles': [
                'SECURITY_ADMINISTRATOR',
                'OPERATOR'
            ],
            'verbose_name': 'test_group_1'
        },
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_user_add 1'] = {
    'addGroupUsers': {
        'group': {
            'assigned_users': [
                {
                    'email': None,
                    'username': 'vdiadmin'
                }
            ],
            'possible_users': [
            ],
            'verbose_name': 'test_group_1'
        },
        'ok': True
    }
}

snapshots['TestGroupSchema.test_group_user_remove 1'] = {
    'removeGroupUsers': {
        'group': {
            'assigned_users': [
            ],
            'possible_users': [
                {
                    'email': None
                }
            ],
            'verbose_name': 'test_group_1'
        },
        'ok': True
    }
}
