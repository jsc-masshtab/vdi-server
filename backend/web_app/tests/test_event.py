import pytest

from datetime import datetime, timedelta

from web_app.tests.fixtures import fixt_controller, fixt_launch_workers, fixt_db, fixt_redis_client, fixt_auth_context, fixt_user, fixt_veil_client  # noqa
from web_app.tests.utils import execute_scheme
from web_app.journal.schema import event_schema
from common.models.auth import Group, Role
from common.models.event import Event
from common.settings import PAM_AUTH
from web_app.auth.user_schema import user_schema

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.creator,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


@pytest.mark.asyncio
async def test_event_users(fixt_db, fixt_auth_context, fixt_user):
    """Список пользователей в журнале доступен пользователю с ролью OPERATOR."""
    try:

        query = """mutation {
                             addUserRole(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", roles: [%s]){
                               user{
                                 username,
                                 assigned_roles,
                                 possible_roles
                               },
                               ok
                             }
                           }""" % Role.OPERATOR.value
        await execute_scheme(user_schema, query, context=fixt_auth_context)

        query = """{
                  users{
                  username,
                  id}
                }"""

        executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
    except:  # noqa
        raise
    returned_users = executed["users"]
    assert returned_users

    for user_rec in returned_users:
        if user_rec['username'] == 'vdiadmin':
            assert True
            break
    else:
        raise AssertionError()


@pytest.mark.asyncio
async def test_events_count(fixt_db, fixt_auth_context, fixt_user):
    query = """{
                count(event_type: 0)
            }"""
    executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
    assert executed["count"] > 1


@pytest.mark.asyncio
async def test_entity_types(fixt_db, fixt_auth_context, fixt_user):
    query = """{
                entity_types
            }"""
    executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
    entity_types_list = executed["entity_types"]
    assert len(entity_types_list) >= 5


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
async def test_event(snapshot, fixt_db, fixt_auth_context):  # noqa
    event_id = await Event.select("id").gino.first()
    query = """{
                  event(id: "%s") {
                    id
                    event_type
                    message,
                    description,
                    user
                  }
                }""" % str(event_id[0])

    executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
    assert executed["event"]["id"] == str(event_id[0])


@pytest.mark.asyncio
async def test_events_ordering(snapshot, fixt_db, fixt_auth_context):  # noqa
    fst = datetime.now() - timedelta(minutes=181)
    lst = fst + timedelta(minutes=182)

    ordering_list = [
        "user",
        "created"
    ]
    for ordering in ordering_list:
        query = """{
                      events(limit: 5, offset: 0, event_type: 0, start_date: "%sZ", end_date: "%sZ", user: "test_admin", ordering: "%s") {
                        event_type
                        message,
                        description,
                        user
                      }
                    }""" % (
            fst.replace(microsecond=0).isoformat(),
            lst.replace(microsecond=0).isoformat(),
            ordering
        )

        executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)


# @pytest.mark.asyncio
# async def test_veil_events(snapshot, fixt_launch_workers, fixt_controller, fixt_db, fixt_auth_context):  # noqa
#     controller_id = fixt_controller["controller_id"]
#     query = """{
#                 veil_events(controller: "%s") {
#                   id
#                   message
#                 }
#             }""" % controller_id
#     executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
#     snapshot.assert_match(executed)
#
#     query = """{
#                 veil_events_count(controller: "%s")
#             }""" % controller_id
#     executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
#     snapshot.assert_match(executed)


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


@pytest.mark.asyncio
async def test_get_and_change_journal_settings(snapshot, fixt_db, fixt_user, fixt_auth_context):  # noqa
    period_list = [
        "day",
        "week",
        "month",
        "year"
    ]
    for period in period_list:
        qu = ("""mutation {
                      changeJournalSettings(by_count: false, period: "%s") {
                        ok
                      }
                 }""" % period)
        executed = await execute_scheme(event_schema, qu, context=fixt_auth_context)
        assert executed["changeJournalSettings"]["ok"]

    qu = """mutation {
                      changeJournalSettings(by_count: true, count: 1000, dir_path: "/tmp/") {
                        ok
                      }
                 }"""
    executed = await execute_scheme(event_schema, qu, context=fixt_auth_context)
    assert executed["changeJournalSettings"]["ok"]

    query = """{
                  journal_settings {
                    period
                    by_count
                    count
                    dir_path
                  }
                }"""
    executed = await execute_scheme(event_schema, query, context=fixt_auth_context)
    snapshot.assert_match(executed)
