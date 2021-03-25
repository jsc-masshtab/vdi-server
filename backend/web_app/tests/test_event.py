import pytest

from datetime import datetime, timedelta

from web_app.tests.fixtures import fixt_db, fixt_auth_context, fixt_user  # noqa
from web_app.tests.utils import execute_scheme
from web_app.journal.schema import event_schema
from common.models.auth import Group
from common.models.event import Event
from common.settings import PAM_AUTH

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.creator,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


@pytest.mark.asyncio
async def test_event_creator(snapshot, fixt_db, fixt_auth_context):  # noqa
    fst = datetime.now() - timedelta(minutes=181)
    lst = fst + timedelta(minutes=182)

    await Group.soft_create("test", "test_admin")

    try:
        query = """{
                  events(limit: 5, offset: 0, event_type: 0, start_date: "%sZ", end_date: "%sZ", user: "test_admin") {
                    event_type
                    message,
                    description,
                    user
                  }
                }""" % (
            fst.replace(microsecond=0).isoformat(),
            lst.replace(microsecond=0).isoformat(),
        )

        executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)
    except:  # noqa
        raise
    finally:
        await Event.delete.where(Event.user == "test_admin").gino.status()
        group = await Group.get_object(
            include_inactive=True,
            extra_field_name="verbose_name",
            extra_field_value="test",
        )
        await group.delete()


@pytest.mark.asyncio
async def test_export_journal(fixt_db, fixt_user, fixt_auth_context):  # noqa
    start = datetime.now() - timedelta(days=1)
    finish = datetime.now() + timedelta(minutes=1)
    qu = """mutation {
              eventExport(start: "%sZ", finish: "%sZ", journal_path: "/tmp/") {
                ok
              }
         }""" % (
        start.replace(microsecond=0).isoformat(),
        finish.replace(microsecond=0).isoformat(),
    )
    executed = await execute_scheme(event_schema, qu, context=fixt_auth_context)
    assert executed["eventExport"]["ok"]
