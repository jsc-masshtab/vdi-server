# -*- coding: utf-8 -*-
"""Group GraphQL schema tests
   Snapshots are created on empty database.
   If you have local groups - output for list will be different."""

import pytest

from web_app.tests.fixtures import fixt_db, fixt_auth_context, fixt_group  # noqa
from web_app.tests.utils import execute_scheme, ExecError
from web_app.auth.group_schema import group_schema
from common.models.auth import Group
from common.settings import PAM_AUTH

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.groups,
    pytest.mark.auth,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


@pytest.mark.usefixtures("fixt_db", "fixt_group")
class TestGroupSchema:
    async def test_group_list(self, snapshot, fixt_auth_context):  # noqa
        query = """{
          groups {
            verbose_name
            description
            assigned_users {
              email
              username
            }
            possible_users {
                email
                username
            }
          }
        }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_group_get_by_id(self, snapshot, fixt_auth_context):  # noqa
        # Хардкод идентификатора лежит в фикстуре.
        query = """{
                  group(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4") {
                    id
                    verbose_name
                    description
                    assigned_users {
                      email
                      username
                    }
                    possible_users {
                        email
                        username
                    }
                  }
                }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_group_create(self, snapshot, fixt_auth_context):  # noqa

        query = """mutation{createGroup(verbose_name: "test group 2"){
                  group{
                    verbose_name,
                    assigned_users{
                      email
                    }
                  },
                  ok
                }}"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)
        await Group.delete.where(Group.verbose_name == "test group 2").gino.status()
        assert True

    async def test_group_create_bad(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation{createGroup(verbose_name: "test_group_1"){
                          group{
                            verbose_name,
                            assigned_users{
                              email
                            }
                          },
                          ok
                        }}"""
        try:
            await execute_scheme(group_schema, query, context=fixt_auth_context)
        except ExecError as E:
            assert "duplicate key value violates unique constraint" in str(E)
        else:
            raise AssertionError

    async def test_group_edit(self, snapshot, fixt_auth_context):  # noqa

        query = """mutation {
                      updateGroup(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                        verbose_name: "test group updated") {
                        group {
                          verbose_name
                          assigned_users {
                            email
                          }
                        }
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_group_delete(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                      deleteGroup(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4") {
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_group_delete_by_guid(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                      deleteGroup(ad_guid: "10913d5d-ba7a-4049-88c5-769267a6cbe5") {
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_group_delete_by_wrong_guid(
        self, snapshot, fixt_auth_context
    ):  # noqa
        query = """mutation {
                      deleteGroup(ad_guid: "10913d5d-ba7a-4049-88c5-769267a6cbe7") {
                        ok
                      }
                    }"""
        try:
            await execute_scheme(group_schema, query, context=fixt_auth_context)
        except ExecError as E:
            assert "[GraphQLLocatedError('Отсутствует такая группа.',)]" in str(E)
        else:
            raise AssertionError()

    async def test_group_delete_by_id_and_guid(
        self, snapshot, fixt_auth_context
    ):  # noqa
        query = """mutation {
                      deleteGroup(ad_guid: "10913d5d-ba7a-4049-88c5-769267a6cbe7",
                       id: "10913d5d-ba7a-4049-88c5-769267a6cbe7") {
                        ok
                      }
                    }"""
        try:
            await execute_scheme(group_schema, query, context=fixt_auth_context)
        except ExecError as E:
            assert "Укажите Group.id или Group.ad_guid. Не оба." in str(E)
        else:
            raise AssertionError()

    async def test_group_user_add(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                      addGroupUsers(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                                    users: ["f9599771-cc95-45e5-9ae5-c8177b796aff"]) {
                        group {
                          verbose_name
                          assigned_users {
                            username
                            email
                          }
                          possible_users {
                            username
                            email
                          }
                        }
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_group_user_remove(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                      removeGroupUsers(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                                    users: ["f9599771-cc95-45e5-9ae5-c8177b796aff"]) {
                        group {
                          verbose_name
                          assigned_users {
                            email
                          }
                          possible_users {
                            email
                          }
                        }
                        ok
                      }
                    }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_group_role(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                    addGroupRole(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                    roles: [ADMINISTRATOR, OPERATOR]) {
                    ok,
                    group {
                        verbose_name
                        assigned_roles
                        possible_roles
                        }
                    }
                    }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)
        query = """mutation {
                            removeGroupRole(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                            roles: [OPERATOR]) {
                            ok,
                            group {
                                verbose_name
                                assigned_roles
                                possible_roles
                                }
                            }
                            }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_group_permission(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                    addGroupPermission(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                    permissions: [USB_REDIR, FOLDERS_REDIR]) {
                    ok,
                    group {
                        verbose_name
                        assigned_permissions
                        possible_permissions
                        }
                    }
                    }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        assigned_permissions_list = executed["addGroupPermission"]["group"][
            "assigned_permissions"
        ]
        assert len(assigned_permissions_list) == 2
        assert "FOLDERS_REDIR" in assigned_permissions_list
        assert "USB_REDIR" in assigned_permissions_list
        query = """mutation {
                            removeGroupPermission(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                            permissions: [USB_REDIR]) {
                            ok,
                            group {
                                verbose_name
                                assigned_permissions
                                possible_permissions
                                }
                            }
                            }"""
        executed = await execute_scheme(group_schema, query, context=fixt_auth_context)
        assigned_permissions_list = executed["removeGroupPermission"]["group"][
            "assigned_permissions"
        ]
        assert len(assigned_permissions_list) == 1
        assert "FOLDERS_REDIR" in assigned_permissions_list
