# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestUserSchema.test_users_list 1'] = {
    'users': [
        {
            'email': 'admin@admin.admin',
            'first_name': None,
            'is_active': True,
            'is_superuser': True,
            'last_name': None,
            'username': 'admin'
        }
    ]
}

snapshots['TestUserSchema.test_user_create 1'] = {
    'createUser': {
        'ok': True,
        'user': {
            'email': 'a.devyatkin@mashtab.org',
            'is_superuser': False,
            'password': '********',
            'username': 'devyatkin'
        }
    }
}

snapshots['TestUserSchema.test_user_edit 1'] = {
    'updateUser': {
        'ok': True,
        'user': {
            'email': 'test@test.ru',
            'first_name': 'test_firstname',
            'is_superuser': False,
            'last_name': 'test_lastname',
            'username': 'devyatkin'
        }
    }
}

snapshots['TestUserSchema.test_user_change_password 1'] = {
    'changeUserPassword': {
        'ok': True
    }
}

snapshots['TestUserSchema.test_user_deactivate 1'] = {
    'deactivateUser': {
        'ok': True
    }
}

snapshots['TestUserSchema.test_user_activate 1'] = {
    'activateUser': {
        'ok': True
    }
}

snapshots['TestUserSchema.test_users_get_by_username 1'] = {
    'user': {
        'email': 'admin@admin.admin',
        'first_name': None,
        'is_active': True,
        'is_superuser': True,
        'last_name': None,
        'username': 'admin'
    }
}

snapshots['TestUserSchema.test_users_get_by_id 1'] = {
    'user': {
        'email': 'admin@admin.admin',
        'first_name': None,
        'is_active': True,
        'is_superuser': True,
        'last_name': None,
        'username': 'admin'
    }
}

snapshots['TestUserSchema.test_user_role 1'] = {
    'addUserRole': {
        'ok': True,
        'user': {
            'assigned_roles': [
                'VM_OPERATOR'
            ],
            'possible_roles': [
                'READ_ONLY',
                'ADMINISTRATOR',
                'SECURITY_ADMINISTRATOR',
                'VM_ADMINISTRATOR',
                'NETWORK_ADMINISTRATOR',
                'STORAGE_ADMINISTRATOR'
            ],
            'username': 'test_user'
        }
    }
}

snapshots['TestUserSchema.test_user_role 2'] = {
    'removeUserRole': {
        'ok': True,
        'user': {
            'assigned_roles': [
            ],
            'possible_roles': [
                'READ_ONLY',
                'ADMINISTRATOR',
                'SECURITY_ADMINISTRATOR',
                'VM_ADMINISTRATOR',
                'NETWORK_ADMINISTRATOR',
                'STORAGE_ADMINISTRATOR',
                'VM_OPERATOR'
            ],
            'username': 'test_user'
        }
    }
}