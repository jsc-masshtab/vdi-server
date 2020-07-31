# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestVmPermissionsSchema.test_vm_user_permission 1'] = {
    'assignVmToUser': {
        'ok': True,
        'vm': {
            'user': {
                'username': 'test_user'
            }
        }
    }
}

snapshots['TestVmPermissionsSchema.test_vm_user_permission 2'] = {
    'freeVmFromUser': {
        'ok': True
    }
}
