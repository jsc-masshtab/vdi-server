# -*- coding: utf-8 -*-
"""Group GraphQL schema tests
   Snapshots are created on empty database.
   If you have local groups - output for list will be different."""

import pytest

from tests.utils import execute_scheme, ExecError
from tests.fixtures import fixt_db, auth_context_fixture, fixt_group  # noqa

from user.group_schema import group_schema
from user.models import Group

pytestmark = [pytest.mark.asyncio, pytest.mark.groups, pytest.mark.auth]


@pytest.mark.usefixtures('fixt_db', 'fixt_group')
class TestGroupSchema:

    async def test_group_list(self, snapshot, auth_context_fixture):  # noqa
        query = """{
          groups {
            verbose_name
            description
            users {
              email
              username
            }
          }
        }"""
        executed = await execute_scheme(group_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_group_get_by_id(self, snapshot, auth_context_fixture):  # noqa
        # Хардкод идентификатора лежит в фикстуре.
        query = """{
                  group(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4") {
                    id
                    verbose_name
                    description
                    users {
                      email
                      username
                    }
                  }
                }"""
        executed = await execute_scheme(group_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_group_create(self, snapshot, auth_context_fixture):  # noqa

        query = """mutation{createGroup(verbose_name: "test group 2"){
                  group{
                    verbose_name,
                    users{
                      email
                    }
                  },
                  ok
                }}"""
        executed = await execute_scheme(group_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)
        await Group.delete.where(Group.verbose_name == 'test group 2').gino.status()
        assert True

    async def test_group_create_bad(self, snapshot, auth_context_fixture):  # noqa
        query = """mutation{createGroup(verbose_name: "test_group_1"){
                          group{
                            verbose_name,
                            users{
                              email
                            }
                          },
                          ok
                        }}"""
        try:
            await execute_scheme(group_schema, query, context=auth_context_fixture)
        except ExecError as E:
            assert 'duplicate key value violates unique constraint' in str(E)
        else:
            raise AssertionError

    async def test_group_edit(self, snapshot, auth_context_fixture):  # noqa

        query = """mutation {
                      updateGroup(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                        verbose_name: "test group updated") {
                        group {
                          verbose_name
                          users {
                            email
                          }
                        }
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_group_delete(self, snapshot, auth_context_fixture):  # noqa
        query = """mutation {
                      deleteGroup(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4") {
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_group_user_add(self, snapshot, auth_context_fixture):  # noqa
        query = """mutation {
                      addGroupUser(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                                    users: ["f9599771-cc95-45e4-9ae5-c8177b796aff"]) {
                        group {
                          verbose_name
                          users {
                            email
                          }
                        }
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_group_user_remove(self, snapshot, auth_context_fixture):  # noqa
        query = """mutation {
                      removeGroupUser(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                                    users: ["f9599771-cc95-45e4-9ae5-c8177b796aff"]) {
                        group {
                          verbose_name
                          users {
                            email
                          }
                        }
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)
