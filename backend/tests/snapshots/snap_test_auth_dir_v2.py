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

snapshots['TestAuthenticationDirectorySchema.test_auth_dirs_list 1'] = {
    'auth_dirs': [
        {
            'admin_server': '',
            'connection_type': 'LDAP',
            'description': '',
            'directory_type': 'ActiveDirectory',
            'directory_url': 'ldap://192.168.11.180',
            'domain_name': 'bazalt.team',
            'kdc_urls': [
                ''
            ],
            'service_password': '********',
            'service_username': '',
            'sso': False,
            'status': 'ACTIVE',
            'subdomain_name': '',
            'verbose_name': 'Bazalt'
        }
    ]
}

snapshots['TestAuthenticationDirectorySchema.test_auth_dirs_get_by_id 1'] = {
    'auth_dir': {
        'admin_server': '',
        'connection_type': 'LDAP',
        'description': '',
        'directory_type': 'ActiveDirectory',
        'directory_url': 'ldap://192.168.11.180',
        'domain_name': 'bazalt.team',
        'kdc_urls': [
            ''
        ],
        'service_password': '********',
        'service_username': '',
        'sso': False,
        'status': 'ACTIVE',
        'subdomain_name': '',
        'verbose_name': 'Bazalt'
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
