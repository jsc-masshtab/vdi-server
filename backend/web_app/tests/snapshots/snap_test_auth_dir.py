# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAuthenticationDirectoryCreate.test_auth_dir_no_pass_create 1'] = {
    'createAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryCreate.test_auth_dir_bad_pass_create 1'] = {
    'createAuthDir': {
        'auth_dir': {
            'status': 'BAD_AUTH'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryCreate.test_auth_dir_bad_address_create 1'] = {
    'createAuthDir': {
        'auth_dir': {
            'status': 'FAILED'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryQuery.test_auth_dirs_list 1'] = {
    'auth_dirs': [
        {
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'status': 'ACTIVE',
            'verbose_name': 'test_auth_dir'
        }
    ]
}

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_by_id 1'] = {
    'auth_dir': {
        'connection_type': 'LDAP',
        'description': None,
        'directory_type': 'ActiveDirectory',
        'directory_url': 'ldap://192.168.11.180',
        'domain_name': 'bazalt.team',
        'mappings': [
        ],
        'verbose_name': 'test_auth_dir'
    }
}

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_possible_ad_groups_no_pass 1'] = {
    'auth_dir': {
        'assigned_ad_groups': [
        ],
        'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
        'possible_ad_groups': [
        ],
        'status': 'ACTIVE'
    }
}

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_possible_ad_groups_bad_pass 1'] = {
    'auth_dir': {
        'assigned_ad_groups': [
        ],
        'id': '10913d5d-ba7a-4049-88c5-769267a6cbe6',
        'possible_ad_groups': [
        ],
        'status': 'BAD_AUTH'
    }
}

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_group_members_no_pass 1'] = {
    'group_members': [
    ]
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

snapshots['TestAuthenticationDirectoryCreate.test_auth_dir_create_no_pass 1'] = {
    'createAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryDelete.test_drop_auth_dir_with_synced_group 1'] = {
    'deleteAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryDelete.test_drop_auth_dir 1'] = {
    'deleteAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryEdit.test_auth_dir_edit 1'] = {
    'updateAuthDir': {
        'auth_dir': {
            'status': 'ACTIVE'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryEdit.test_auth_dir_edit_bad_pass 1'] = {
    'updateAuthDir': {
        'auth_dir': {
            'status': 'ACTIVE'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryEdit.test_auth_dir_edit_bad_address 1'] = {
    'updateAuthDir': {
        'auth_dir': {
            'status': 'FAILED'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryMappings.test_add_auth_dir_mapp 1'] = {
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

snapshots['TestAuthenticationDirectoryMappings.test_edit_auth_dir_mapp 1'] = {
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

snapshots['TestAuthenticationDirectoryMappings.test_del_auth_dir_mapp 1'] = {
    'deleteAuthDirMapping': {
        'auth_dir': {
            'id': '10913d5d-ba7a-4049-88c5-769267a6cbe4',
            'mappings': [
            ]
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_check 1'] = {
    'testAuthDir': {
        'auth_dir': {
            'status': 'ACTIVE'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_with_pass_check 1'] = {
    'testAuthDir': {
        'auth_dir': {
            'status': 'ACTIVE'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_with_bad_pass_check 1'] = {
    'testAuthDir': {
        'auth_dir': {
            'status': 'BAD_AUTH'
        },
        'ok': False
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_sync_new_only_group 1'] = {
    'syncAuthDirGroupUsers': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_sync_group_and_users 1'] = {
    'syncAuthDirGroupUsers': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_group_members 1'] = {
    'group_members': [
        {
            'email': None,
            'first_name': 'administrator',
            'last_name': None,
            'username': 'administrator'
        },
        {
            'email': None,
            'first_name': 'o.krutov',
            'last_name': None,
            'username': 'o.krutov'
        },
        {
            'email': 'r.danilov@mashtab.org',
            'first_name': 'Roman',
            'last_name': 'Danilov',
            'username': 'r.danilov'
        },
        {
            'email': None,
            'first_name': 'Denis',
            'last_name': 'Gubin',
            'username': 'd.gubin'
        },
        {
            'email': None,
            'first_name': 'Александр',
            'last_name': 'Моисеев',
            'username': 'a.moiseev'
        },
        {
            'email': None,
            'first_name': 'Alex',
            'last_name': 'Devyatkin',
            'username': 'a.devyatkin'
        }
    ]
}

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_possible_ad_groups 1'] = {
    'auth_dir': {
        'assigned_ad_groups': [
        ],
        'id': '10913d5d-ba7a-4049-88c5-769267a6cbe5',
        'possible_ad_groups': [
            {
                'ad_guid': '4f49ec7e-88a3-4576-bb30-86fea00f412b',
                'verbose_name': 'DnsUpdateProxy'
            },
            {
                'ad_guid': '066e3e56-f12e-4c7e-a2a1-b1a81351e9f4',
                'verbose_name': 'HorizonViewAdmins'
            },
            {
                'ad_guid': 'df4745bd-6a47-47bf-b5c7-43cf7e266068',
                'verbose_name': 'veil-admins'
            },
            {
                'ad_guid': '4661fa0b-fb28-48bb-84fe-9b3193a6b571',
                'verbose_name': 'veil-ad-users'
            },
            {
                'ad_guid': 'e006a986-17e6-4817-b2cc-7e70bcf01222',
                'verbose_name': 'LINUX'
            },
            {
                'ad_guid': 'cff4b40c-cc7f-4854-b3d9-d87dabd75411',
                'verbose_name': 'vdi-autopool-test'
            }
        ],
        'status': 'ACTIVE'
    }
}
