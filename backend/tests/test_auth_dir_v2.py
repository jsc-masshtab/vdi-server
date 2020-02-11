# -*- coding: utf-8 -*-
"""AuthenticationDirectory GraphQL schema tests
   Snapshots are created on empty database.
   If you have local users - output for list may be different."""

import pytest

from tests.utils import execute_scheme, ExecError

from auth.authentication_directory.auth_dir_schema import auth_dir_schema
from auth.authentication_directory.models import AuthenticationDirectory

pytestmark = [pytest.mark.asyncio, pytest.mark.auth_dir, pytest.mark.auth]


@pytest.mark.usefixtures('fixt_db')
class TestAuthenticationDirectorySchema:

    async def test_auth_dir_create(self, snapshot, auth_context_fixture):  # noqa
        query = """mutation {createAuthDir(
                      domain_name: "bazalt.team" #!Обязательное поле
                      verbose_name: "Bazalt" #!Обязательное поле
                      directory_url: "ldap://192.168.11.180" #!Обязательное поле
                      description: ""
                      connection_type: LDAP
                      directory_type: ActiveDirectory
                      service_username: ""
                      service_password: ""
                      admin_server: ""
                      subdomain_name: ""
                      kdc_urls: ""
                      sso: false
                    ) {
                      ok
                    }}"""
        executed = await execute_scheme(auth_dir_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_auth_dir_create_bad(self, auth_context_fixture):  # noqa
        query = """mutation {createAuthDir(
                      domain_name: "bazalt.team" #!Обязательное поле
                      verbose_name: "Bazalt" #!Обязательное поле
                      directory_url: "ldap://192.168.11.180" #!Обязательное поле
                      description: ""
                      connection_type: LDAP
                      directory_type: ActiveDirectory
                      service_username: ""
                      service_password: ""
                      admin_server: ""
                      subdomain_name: ""
                      kdc_urls: ""
                      sso: false
                    ) {
                      ok
                    }}"""
        try:
            await execute_scheme(auth_dir_schema, query, context=auth_context_fixture)
        except ExecError as E:
            assert 'More than one authentication directory can not be created.' in str(E)

    async def test_auth_dirs_list(self, snapshot, auth_context_fixture):  # noqa
        query = """query{auth_dirs {
                            verbose_name
                            directory_url
                            connection_type
                            description
                            directory_type
                            domain_name
                            # SSO fields
                            subdomain_name
                            service_username
                            service_password
                            admin_server
                            kdc_urls
                            status
                            sso
                        }}"""
        executed = await execute_scheme(auth_dir_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_auth_dirs_get_by_id(self, snapshot, auth_context_fixture):  # noqa
        auth_dir = await AuthenticationDirectory.get_object(extra_field_name='verbose_name', extra_field_value='Bazalt',
                                                            include_inactive=True)
        query = """{auth_dir(id: "%s") {
                        verbose_name
                        directory_url
                        connection_type
                        description
                        directory_type
                        domain_name
                        # SSO fields
                        subdomain_name
                        service_username
                        service_password
                        admin_server
                        kdc_urls
                        status
                        sso
                    }}""" % auth_dir.id
        executed = await execute_scheme(auth_dir_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_auth_dir_check(self, snapshot, auth_context_fixture):  # noqa
        auth_dir = await AuthenticationDirectory.get_object(extra_field_name='verbose_name', extra_field_value='Bazalt',
                                                            include_inactive=True)
        query = """mutation {
                        testAuthDir(id: "%s")
                    {
                      ok
                    }}""" % auth_dir.id
        executed = await execute_scheme(auth_dir_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_auth_dir_edit(self, snapshot, auth_context_fixture):  # noqa
        auth_dir = await AuthenticationDirectory.get_object(extra_field_name='verbose_name', extra_field_value='Bazalt',
                                                            include_inactive=True)
        query = """mutation {updateAuthDir(
                      id: "%s"
                      verbose_name: "tst_verbose_name"
                      directory_type: ActiveDirectory
                      description: "test"
                      service_username: "service_username"
                      service_password: "servicePassword123!!"
                      domain_name: "bazalt.team"
                      connection_type: LDAP
                      subdomain_name: "subdomain_name"
                      directory_url: "ldap://192.168.10.10"
                      sso: true
                      admin_server: "admin_server"
                    ) {
                      ok,
                    }}""" % auth_dir.id
        executed = await execute_scheme(auth_dir_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)

    async def test_drop_auth_dir(self, snapshot, auth_context_fixture):  # noqa
        auth_dir = await AuthenticationDirectory.get_object(extra_field_name='verbose_name',
                                                            extra_field_value='tst_verbose_name',
                                                            include_inactive=True)
        query = """mutation {deleteAuthDir(id: "%s") {
                      ok
                    }}""" % auth_dir.id
        executed = await execute_scheme(auth_dir_schema, query, context=auth_context_fixture)
        snapshot.assert_match(executed)
