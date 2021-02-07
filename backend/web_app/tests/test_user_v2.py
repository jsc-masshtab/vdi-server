# -*- coding: utf-8 -*-
"""User GraphQL schema tests
   Snapshots are created on empty database.
   If you have local users - output for list will be different."""

import pytest

from web_app.tests.fixtures import fixt_db, fixt_auth_context, fixt_user  # noqa
from web_app.tests.utils import execute_scheme, ExecError
from web_app.auth.user_schema import user_schema
from common.models.auth import User
from common.settings import PAM_AUTH

pytestmark = [pytest.mark.asyncio, pytest.mark.users, pytest.mark.auth,
              pytest.mark.skipif(PAM_AUTH, reason="not finished yet")]


@pytest.mark.usefixtures('fixt_db')
class TestUserSchema:

    async def test_users_list(self, snapshot, fixt_auth_context):  # noqa
        query = """{
          users{
            is_active
            is_superuser
            username
          }
        }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_users_get_by_id(self, snapshot, fixt_auth_context):  # noqa
        query = """{
                user(id: "f9599771-cc95-45e4-9ae5-c8177b796aff"){
                    username,
                    email,
                    last_name,
                    first_name,
                    is_superuser,
                    is_active
                    }
                }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_users_get_by_username(self, snapshot, fixt_auth_context):  # noqa
        query = """{
              user (
                    username: "admin"
                    )
                {
                    username,
                    email,
                    last_name,
                    first_name,
                    is_superuser,
                    is_active
                }
            }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_user_create(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                createUser(
                username: "devyatkin",  # !обязательное поле
                password: "qwQ123$%",  # !обязательное поле
                email: "a.devyatkin@mashtab.org",  # !обязательное поле
                last_name: "Devyatkin",  # !обязательное поле
                first_name: "Aleksey",  # !обязательное поле
                is_superuser: false  # Признак администратора
                )
                {
                ok,
                user {
                    username,
                    email,
                    password,
                    is_superuser
                    }
                }
                }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_user_create_bad(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                createUser(
                username: "devyatkin",
                password: "qwQ123$%",
                email: "a.devyatkin@mashtab.org",
                last_name: "Devyatkin",
                first_name: "Aleksey",
                is_superuser: false
                )
                {
                ok,
                user {
                    username,
                    email,
                    password,
                    is_superuser
                    }
                }
                }"""
        try:
            await execute_scheme(user_schema, query, context=fixt_auth_context)
        except ExecError as E:
            assert 'Email a.devyatkin@mashtab.org занят.' in str(E)

    async def test_user_edit(self, snapshot, fixt_auth_context):  # noqa
        user_obj = await User.get_object(extra_field_name='username', extra_field_value='devyatkin',
                                         include_inactive=True)
        query = """mutation {
                      updateUser(
                        id: "%s", # !обязательное поле
                        first_name: "test_firstname",
                        email: "test@test.ru",
                        last_name: "test_lastname",
                      ) {
                        ok,
                        user{
                          username,
                          email,
                          first_name,
                          last_name,
                          is_superuser
                        }
                      }
                    }""" % user_obj.id
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_user_change_password(self, snapshot, fixt_auth_context):  # noqa
        user_obj = await User.get_object(extra_field_name='username', extra_field_value='devyatkin',
                                         include_inactive=True)
        query = """mutation {
                    changeUserPassword(id: "%s",
                    password: "zpt36qQ!@"
                    )
                    {
                      ok
                    }
                }""" % user_obj.id
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_user_deactivate(self, snapshot, fixt_auth_context):  # noqa
        user_obj = await User.get_object(extra_field_name='username', extra_field_value='devyatkin',
                                         include_inactive=True)
        query = """mutation {
                        deactivateUser(id: "%s")
                        {
                          ok
                        }
                    }""" % user_obj.id
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_user_activate(self, snapshot, fixt_auth_context):  # noqa
        query = """mutation {
                        activateUser(id: "f9599771-cc95-45e4-9ae5-c8177b796aff")
                        {
                          ok
                        }
                    }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_drop_user(self):
        user = await User.get_object(include_inactive=True, extra_field_name='username', extra_field_value='devyatkin')
        await user.delete()
        assert True

    async def test_user_role(self, snapshot, fixt_auth_context, fixt_user):  # noqa
        query = """mutation {
                      addUserRole(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", roles: [OPERATOR]){
                        user{
                          username,
                          assigned_roles,
                          possible_roles
                        },
                        ok
                      }
                    }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)
        query = """mutation {
                      removeUserRole(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", roles: [OPERATOR]){
                        user{
                          username,
                          assigned_roles,
                          possible_roles
                        },
                        ok
                      }
                    }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

    async def test_user_permission(self, snapshot, fixt_auth_context, fixt_user):  # noqa

        # По умолчанию новые пользователи имеют все права
        query = """mutation {
                      removeUserPermission(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", permissions: [USB_REDIR]){
                        user{
                          username,
                          assigned_permissions,
                          possible_permissions
                        },
                        ok
                      }
                    }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        # Permissions are Set. Snapshot would`t work.
        assigned_permissions_list = executed['removeUserPermission']['user']['assigned_permissions']
        assert len(assigned_permissions_list) == 2
        assert 'SHARED_CLIPBOARD' in assigned_permissions_list
        assert 'FOLDERS_REDIR' in assigned_permissions_list

        query = """mutation {
                      addUserPermission(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", permissions: [USB_REDIR]){
                        user{
                          username,
                          assigned_permissions,
                          possible_permissions
                        },
                        ok
                      }
                    }"""
        executed = await execute_scheme(user_schema, query, context=fixt_auth_context)
        assigned_permissions_list = executed['addUserPermission']['user']['assigned_permissions']
        assert len(assigned_permissions_list) == 3
        # Permissions are Set. Snapshot would`t work.
        assert 'USB_REDIR' in assigned_permissions_list
        assert 'SHARED_CLIPBOARD' in assigned_permissions_list
        assert 'FOLDERS_REDIR' in assigned_permissions_list
