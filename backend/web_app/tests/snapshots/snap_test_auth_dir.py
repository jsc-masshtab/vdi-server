# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAuthenticationDirectoryCreate.test_auth_dir_bad_address_create 1'] = {
    'createAuthDir': {
        'auth_dir': {
            'status': 'FAILED'
        },
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

snapshots['TestAuthenticationDirectoryCreate.test_auth_dir_create_no_pass 1'] = {
    'createAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryCreate.test_auth_dir_no_pass_create 1'] = {
    'createAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryCreate.test_free_ipa_no_pass_create 1'] = {
    'createAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryDelete.test_drop_auth_dir 1'] = {
    'deleteAuthDir': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryDelete.test_drop_auth_dir_with_synced_group 1'] = {
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

snapshots['TestAuthenticationDirectoryEdit.test_auth_dir_edit_bad_address 1'] = {
    'updateAuthDir': {
        'auth_dir': {
            'status': 'FAILED'
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

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_by_id 1'] = {
    'auth_dir': {
        'connection_type': 'LDAP',
        'dc_str': 'bazalt.local',
        'description': None,
        'directory_type': 'ActiveDirectory',
        'directory_url': 'ldap://192.168.14.167',
        'domain_name': 'BAZALT',
        'mappings': [
        ],
        'verbose_name': 'test_auth_dir'
    }
}

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_possible_ad_groups 1'] = {
    'auth_dir': {
        'assigned_ad_groups': [
        ],
        'id': '10913d5d-ba7a-4049-88c5-769267a6cbe5',
        'possible_ad_groups': [
            {
                'ad_guid': 'd61e64b2-449f-4fd8-89fa-5ee29edde9c7',
                'verbose_name': 'DnsAdmins'
            },
            {
                'ad_guid': '7ed075e1-770d-486d-9518-c689daf4878a',
                'verbose_name': 'DnsUpdateProxy'
            },
            {
                'ad_guid': '16905200-78dc-4811-8833-c80a217fb9d3',
                'verbose_name': 'SSO_Admins'
            },
            {
                'ad_guid': '39b76197-d575-4200-949f-c19af052f82d',
                'verbose_name': 'TestGroupLocal'
            },
            {
                'ad_guid': 'ba9a745b-fdf8-471e-85d6-a7ed0d6fd30c',
                'verbose_name': 'TestGroupUniversal'
            },
            {
                'ad_guid': '992e4139-f98f-464c-af70-42e53b0c49ff',
                'verbose_name': 'VDI_RDP'
            },
            {
                'ad_guid': '01811ba9-a79e-4728-a181-dbd568572b91',
                'verbose_name': 'vdi-autopool-test'
            },
            {
                'ad_guid': '097bba0c-a922-407d-ab95-1d0b9c50801b',
                'verbose_name': 'vdi-autopool-test2'
            },
            {
                'ad_guid': 'ec0efca9-5878-4ab4-bb8f-149af659e115',
                'verbose_name': 'veil-ad-users'
            },
            {
                'ad_guid': '94461754-e8ea-4fbc-9716-f9f8e97e2d82',
                'verbose_name': 'Администраторы DHCP'
            },
            {
                'ad_guid': '166054a6-b8ce-4d01-b025-11b7faef033c',
                'verbose_name': 'Администраторы безопасности'
            },
            {
                'ad_guid': '83aed0e4-3a2a-45db-91ed-6484371a27cc',
                'verbose_name': 'Пользователи DHCP'
            }
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

snapshots['TestAuthenticationDirectoryQuery.test_auth_dir_get_possible_ipa_ad_groups 1'] = {
    'auth_dir': {
        'assigned_ad_groups': [
        ],
        'id': '10923d5d-ba7a-4049-88c5-769267a6cbe5',
        'possible_ad_groups': [
            {
                'ad_guid': 'b19e2d7e-653e-11eb-ac14-02fff06b60b5',
                'verbose_name': 'administrator'
            },
            {
                'ad_guid': '66d03094-652a-11eb-ba09-02fff06b60b5',
                'verbose_name': 'admins'
            },
            {
                'ad_guid': '66eb5144-652a-11eb-b641-02fff06b60b5',
                'verbose_name': 'editors'
            },
            {
                'ad_guid': '66e4c554-652a-11eb-aee9-02fff06b60b5',
                'verbose_name': 'ipausers'
            },
            {
                'ad_guid': 'e9e3dcfe-652c-11eb-a73d-02fff06b60b5',
                'verbose_name': 'read_only'
            },
            {
                'ad_guid': 'dd284a5e-652c-11eb-9bc0-02fff06b60b5',
                'verbose_name': 'security_administrator'
            },
            {
                'ad_guid': 'f53f87e4-652a-11eb-9f6f-02fff06b60b5',
                'verbose_name': 'trust admins'
            },
            {
                'ad_guid': '5a0f5868-652e-11eb-bc98-02fff06b60b5',
                'verbose_name': 'vm_operator'
            }
        ],
        'status': 'ACTIVE'
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

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_check 1'] = {
    'testAuthDir': {
        'auth_dir': {
            'status': 'ACTIVE'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_sync_group_and_users 1'] = {
    'syncAuthDirGroupUsers': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_sync_possible_openldap_users 1'] = {
    'syncOpenLDAPUsers': {
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

snapshots['TestAuthenticationDirectoryUtils.test_auth_dir_with_pass_check 1'] = {
    'testAuthDir': {
        'auth_dir': {
            'status': 'ACTIVE'
        },
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_ipa_sync_group_and_users 1'] = {
    'syncAuthDirGroupUsers': {
        'ok': True
    }
}

snapshots['TestAuthenticationDirectoryUtils.test_ipa_sync_new_only_group 1'] = {
    'syncAuthDirGroupUsers': {
        'ok': True
    }
}
