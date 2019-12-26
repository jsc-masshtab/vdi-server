# -*- coding: utf-8 -*-
"""User GraphQL schema tests
   Snapshots are created on empty database.
   If you have local users - output for list will be different."""

import pytest

from tests.utils import execute_scheme, ExecError
from tests.fixtures import fixt_db, auth_context_fixture

from user.schema import user_schema
from user.models import User

pytestmark = [pytest.mark.asyncio, pytest.mark.users, pytest.mark.auth]


@pytest.mark.usefixtures('fixt_db')
class TestUserSchema:

    async def test_users_list(self, snapshot, auth_context_fixture):
        query = """{
          users{
            email
            first_name
            is_active
            is_superuser
            last_name
            username
          }
        }"""
        executed = await execute_scheme(user_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_users_get_by_id(self, snapshot, auth_context_fixture):
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
        executed = await execute_scheme(user_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_users_get_by_username(self, snapshot, auth_context_fixture):
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
        executed = await execute_scheme(user_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_user_create(self, snapshot, auth_context_fixture):
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
        executed = await execute_scheme(user_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_user_create_bad(self, snapshot, auth_context_fixture):
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
        try:
            await execute_scheme(user_schema, query, context=auth_context_fixture)
        except ExecError as E:
            assert 'duplicate key value violates unique constraint "user_email_key"' in str(E)

    async def test_user_edit(self, snapshot, auth_context_fixture):
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
        executed = await execute_scheme(user_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_user_change_password(self, snapshot, auth_context_fixture):
        user_obj = await User.get_object(extra_field_name='username', extra_field_value='devyatkin',
                                         include_inactive=True)
        query = """mutation {
                    changeUserPassword(id: "%s", # !обязательное поле
                    password: "zpt36qQ!@"  # !обязательное поле
                    )
                    {
                      ok
                    }
                }""" % user_obj.id
        executed = await execute_scheme(user_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_user_deactivate(self, snapshot, auth_context_fixture):
        user_obj = await User.get_object(extra_field_name='username', extra_field_value='devyatkin',
                                         include_inactive=True)
        query = """mutation {
                        deactivateUser(id: "%s")
                        {
                          ok
                        }
                    }""" % user_obj.id
        executed = await execute_scheme(user_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_user_activate(self, snapshot, auth_context_fixture):
        query = """mutation {
                        activateUser(id: "f9599771-cc95-45e4-9ae5-c8177b796aff")
                        {
                          ok
                        }
                    }"""
        executed = await execute_scheme(user_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_drop_user(self):
        user = await User.get_object(include_inactive=True, extra_field_name='username', extra_field_value='devyatkin')
        await user.delete()
        assert True