# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAuthenticationDirectorySchema.test_auth_dir_create 1'] = {
    'createAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_auth_dir_check 1'] = {
    'testAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_auth_dir_edit 1'] = {
    'updateAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_drop_auth_dir 1'] = {
    'deleteAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_auth_dirs_list 1'] = {
    'auth_dirs': [
        {
            'connection_type': 'LDAP',
            'description': '',
            'directory_type': 'ActiveDirectory',
            'directory_url': 'ldap://192.168.11.180',
            'domain_name': 'bazalt.team',
            'mappings': [
            ],
            'verbose_name': 'Bazalt'
        }
    ]
}

snapshots['TestAuthenticationDirectorySchema.test_auth_dirs_get_by_id 1'] = {
    'auth_dir': {
        'connection_type': 'LDAP',
        'description': '',
        'directory_type': 'ActiveDirectory',
        'directory_url': 'ldap://192.168.11.180',
        'domain_name': 'bazalt.team',
        'mappings': [
        ],
        'verbose_name': 'Bazalt'
    }
}

snapshots['TestAuthenticationDirectorySchema.test_add_auth_dir_mapping 1'] = {
    'addAuthDirMapping': {
        'auth_dir': {
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'mappings': [
                {
                    'verbose_name': 'test_mapping2'
                }
            ]
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_edit_auth_dir_mapping 1'] = {
    'editAuthDirMapping': {
        'auth_dir': {
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'mappings': [
                {
                    'assigned_groups': [
                        {
                            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
                        }
                    ],
                    'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                    'possible_groups': [
                    ],
                    'verbose_name': 'editted mapping'
                }
            ]
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_edit_auth_dir_mapp 1'] = {
    'editAuthDirMapping': {
        'auth_dir': {
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'mappings': [
                {
                    'assigned_groups': [
                        {
                            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4'
                        }
                    ],
                    'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
                    'possible_groups': [
                    ],
                    'verbose_name': 'editted mapping'
                }
            ]
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_add_and_delete_auth_dir_mapp 1'] = {
    'addAuthDirMapping': {
        'auth_dir': {
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'mappings': [
                {
                    'verbose_name': 'test_mapping2'
                }
            ]
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_del_auth_dir_mapp 1'] = {
    'deleteAuthDirMapping': {
        'auth_dir': {
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'mappings': [
            ]
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectorySchema.test_add_auth_dir_mapp 1'] = {
    'addAuthDirMapping': {
        'auth_dir': {
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'mappings': [
                {
                    'verbose_name': 'test_mapping2'
                }
            ]
        },
        'ok': True
    }
}
