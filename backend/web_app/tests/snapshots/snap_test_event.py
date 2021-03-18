# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_event_creator 1"] = {
    "events": [
        {
            "description": None,
            "event_type": 0,
            "message": "Группа test создана.",
            "user": "test_admin",
        }
    ]
}
