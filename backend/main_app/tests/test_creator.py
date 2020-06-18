import pytest

from datetime import datetime, timedelta

from tests.fixtures import fixt_db, fixt_auth_context  # noqa
from tests.utils import execute_scheme

from journal.event.schema import event_schema
from auth.models import Group

pytestmark = [pytest.mark.asyncio, pytest.mark.creator]


@pytest.mark.asyncio
async def test_event_creator(snapshot, fixt_db, fixt_auth_context):  # noqa
    fst = datetime.now() - timedelta(minutes=181)
    lst = fst + timedelta(minutes=182)

    await Group.soft_create('test', 'test_admin')

    query = """{
              events(limit: 5, offset: 0, event_type: 0, start_date: "%sZ", end_date: "%sZ", user: "test_admin") {
                event_type
                message,
                description,
                user
              }
            }""" % (fst.replace(microsecond=0).isoformat(), lst.replace(microsecond=0).isoformat())

    executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
    snapshot.assert_match(executed)

    group = await Group.get_object(include_inactive=True, extra_field_name='verbose_name', extra_field_value='test')
    await group.delete()
