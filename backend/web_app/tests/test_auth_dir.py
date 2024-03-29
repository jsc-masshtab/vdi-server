# -*- coding: utf-8 -*-
"""AuthenticationDirectory GraphQL schema tests
   Snapshots are created on empty database.
   If you have local users - output for list may be different."""

import pytest

from web_app.tests.fixtures import (
    fixt_db,  # noqa
    fixt_redis_client,
    fixt_auth_context,  # noqa
    fixt_group,  # noqa
    fixt_local_group,  # noqa
    fixt_auth_dir,  # noqa
    fixt_auth_dir_with_pass,  # noqa
    fixt_auth_dir_with_pass_bad,  # noqa
    fixt_openldap_with_pass,  # noqa
    fixt_mapping,
    fixt_ipa_with_pass,  # noqa
)  # noqa

from web_app.tests.utils import execute_scheme, ExecError

from common.veil.veil_gino import Status
from web_app.auth.authentication_directory.auth_dir_schema import auth_dir_schema
from common.models.authentication_directory import AuthenticationDirectory, Mapping
from common.models.auth import Group, User
from common.settings import PAM_AUTH
from common.languages import _local_

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.auth_dir,
    pytest.mark.auth,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


@pytest.mark.usefixtures("fixt_db")
class TestAuthenticationDirectoryCreate:
    """Опции создания Authentication Directory."""

    async def test_auth_dir_no_pass_create(self, snapshot, fixt_auth_context):  # noqa
        """Проверка создания Authentication Directory без auth."""
        query = """mutation {createAuthDir(
                      domain_name: "BAZALT"
                      dc_str: "bazalt.local"
                      verbose_name: "test"
                      directory_url: "ldap://192.168.14.167"
                      connection_type: LDAP
                      directory_type: ActiveDirectory
                    ) {
                      ok
                    }}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        ad = await AuthenticationDirectory.query.where(
            AuthenticationDirectory.verbose_name == "test"
        ).gino.first()
        assert ad
        await ad.delete()

    async def test_free_ipa_no_pass_create(self, snapshot, fixt_auth_context):  # noqa
        """Проверка создания Free IPA без auth."""
        query = """mutation {createAuthDir(
                      domain_name: "BAZALT"
                      dc_str: "bazalt.auth"
                      verbose_name: "ipa"
                      directory_url: "ldap://192.168.14.83"
                      connection_type: LDAP
                      directory_type: FreeIPA
                    ) {
                      ok
                    }}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        ad = await AuthenticationDirectory.query.where(
            AuthenticationDirectory.verbose_name == "ipa"
        ).gino.first()
        assert ad
        await ad.delete()

    async def test_auth_dir_create_no_pass(self, snapshot, fixt_auth_context):  # noqa
        """Дополнительно проверяет шифрование пароля Authentication Directory."""
        test_password = "Bazalt1!"
        query = """mutation {createAuthDir(
                      domain_name: "BAZALT"
                      dc_str: "bazalt.team"
                      verbose_name: "test"
                      directory_url: "ldap://192.168.14.167"
                      connection_type: LDAP
                      directory_type: ActiveDirectory
                      service_username: "ad120"
                      service_password: "%s"){ok}}""" % (
            test_password,
        )
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        ad = await AuthenticationDirectory.query.where(
            AuthenticationDirectory.verbose_name == "test"
        ).gino.first()
        assert ad
        # Проверка, что пароль зашифровался
        assert ad.service_password != test_password
        await ad.delete()

    async def test_auth_dir_bad_pass_create(self, snapshot, fixt_auth_context):  # noqa
        """При создании с неправильным паролем статус должен быть BAD_AUTH."""
        test_password = "bad"
        query = """mutation {createAuthDir(
                             domain_name: "BAZALT"
                             dc_str: "bazalt.team"
                             verbose_name: "test"
                             directory_url: "ldap://192.168.14.167"
                             connection_type: LDAP
                             directory_type: ActiveDirectory
                             service_username: "ad120"
                             service_password: "%s"){ok,auth_dir{status}}}""" % (
            test_password,
        )
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        ad = await AuthenticationDirectory.query.where(
            AuthenticationDirectory.verbose_name == "test"
        ).gino.first()
        assert ad
        # Проверка избыточна, в ответе GraphQL уже будет статус, но мне так хочется
        assert ad.status == Status.BAD_AUTH
        await ad.delete()

    async def test_auth_dir_bad_address_create(
        self, snapshot, fixt_auth_context
    ):  # noqa
        """При создании с неправильным паролем статус должен быть FAILED."""
        query = """mutation {createAuthDir(
                              domain_name: "BAZALT"
                              dc_str: "bazalt.team"
                              verbose_name: "test"
                              directory_url: "ldap://127.0.0.1"
                              connection_type: LDAP
                              directory_type: ActiveDirectory
                            ){ok,auth_dir{status}}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        ad = await AuthenticationDirectory.query.where(
            AuthenticationDirectory.verbose_name == "test"
        ).gino.first()
        assert ad
        await ad.delete()

    async def test_auth_dir_create_bad(self, fixt_auth_context, fixt_auth_dir):  # noqa
        """Проверяет, что нельзя создать больше 1 записи Authentication Directory."""
        query = """mutation {createAuthDir(
                      domain_name: "BAZALT"
                      dc_str: "bazalt.local"
                      verbose_name: "Bazalt"
                      directory_url: "ldap://192.168.14.167"
                      connection_type: LDAP
                      directory_type: ActiveDirectory
                    ) {
                      ok
                    }}"""
        try:
            await execute_scheme(auth_dir_schema, query, context=fixt_auth_context)
        except ExecError as E:
            assert _local_(
                "More than one authentication directory can not be created."
            ) in str(E)


@pytest.mark.usefixtures("fixt_db")
class TestAuthenticationDirectoryQuery:
    """Проверка опций просмотра информации Authentication Directory."""

    async def test_auth_dirs_list(
        self, snapshot, fixt_auth_context, fixt_auth_dir
    ):  # noqa
        """Проверяем что выводятся поля, которые есть в таблице на фронте."""
        query = """query{auth_dirs{id, verbose_name, status}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_auth_dir_get_by_id(
        self, snapshot, fixt_auth_context, fixt_auth_dir
    ):  # noqa
        """Проверяем что работает поиск по id без service_password."""
        query = """{auth_dir(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4") {
                        verbose_name
                        directory_url
                        connection_type
                        description
                        directory_type
                        domain_name
                        dc_str
                        mappings {
                            id
                            verbose_name
                            description
                            value_type
                            values
                            priority
                            assigned_groups {
                              id
                            }
                            possible_groups {
                              id
                            }
                          }
                    }}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_auth_dir_get_possible_ad_groups(
        self, snapshot, fixt_auth_context, fixt_auth_dir_with_pass
    ):  # noqa
        """Проверяем что работает поиск по id и просмотр доступных для назначения групп."""
        query = """{auth_dir(id: "10913d5d-ba7a-4049-88c5-769267a6cbe5")
        {id,
                    assigned_ad_groups{ad_guid,verbose_name}
                    possible_ad_groups{ad_guid,verbose_name}
                    status}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_auth_dir_get_possible_ad_groups_no_pass(
        self, snapshot, fixt_auth_context, fixt_auth_dir
    ):  # noqa
        """При отсутствующем пароле список групп будет пустой."""
        query = """{auth_dir(id:"10913d5d-ba7a-4049-88c5-769267a6cbe4"){id,
                    assigned_ad_groups{ad_guid,verbose_name},
                    possible_ad_groups{ad_guid,verbose_name},
                    status}}"""
        try:
            await execute_scheme(auth_dir_schema, query, context=fixt_auth_context)
        except Exception as E:
            assert "Имя пользователя и пароль LDAP не могут быть пустыми" in str(E)
        else:
            raise AssertionError()

    async def test_auth_dir_get_possible_ad_groups_bad_pass(
        self, snapshot, fixt_auth_context, fixt_auth_dir_with_pass_bad
    ):  # noqa
        """При неправильном пароле список групп будет пустой."""
        query = """{auth_dir(id:"10913d5d-ba7a-4049-88c5-769267a6cbe6"){id,
                    assigned_ad_groups{ad_guid,verbose_name},
                    possible_ad_groups{ad_guid,verbose_name},
                    status}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_auth_dir_get_possible_ipa_ad_groups(
        self, snapshot, fixt_auth_context, fixt_ipa_with_pass
    ):  # noqa
        """Проверяем что работает поиск по id и просмотр доступных для назначения групп."""
        query = """{auth_dir(id: "10923d5d-ba7a-4049-88c5-769267a6cbe5")
                        {id,
                         assigned_ad_groups{ad_guid,verbose_name}
                         possible_ad_groups{ad_guid,verbose_name}
                         status}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)


@pytest.mark.usefixtures("fixt_db")
class TestAuthenticationDirectoryDelete:
    """Проверка удаления Authentication Directory."""

    async def test_drop_auth_dir(
        self, snapshot, fixt_auth_context, fixt_auth_dir
    ):  # noqa
        """Запись должна удалиться."""
        query = """mutation{deleteAuthDir(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"){ok}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_drop_auth_dir_with_synced_group(
        self, snapshot, fixt_auth_context, fixt_auth_dir, fixt_group
    ):  # noqa
        """Запись должна удалиться, а у группы ad_guid должен обнулиться."""
        # Проверяем, что запись есть
        group = await Group.get("10913d5d-ba7a-4049-88c5-769267a6cbe4")
        assert group
        group_ad_guid = group.ad_guid
        query = """mutation{deleteAuthDir(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"){ok}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        # Актуализируем значение идентификатора из AD
        group = await Group.get("10913d5d-ba7a-4049-88c5-769267a6cbe4")
        assert group_ad_guid != group.ad_guid
        assert group.ad_guid is None


@pytest.mark.usefixtures("fixt_db")
class TestAuthenticationDirectoryEdit:
    """Проверка редактирования Authentication Directory."""

    async def test_auth_dir_edit(
        self, snapshot, fixt_auth_context, fixt_auth_dir
    ):  # noqa
        query = """mutation {updateAuthDir(
                      id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"
                      verbose_name: "tst_verbose_name"
                      directory_type: ActiveDirectory
                      domain_name: "bazalt"
                      dc_str: "bazalt.local"
                    ) {ok, auth_dir{status}}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_auth_dir_edit_bad_address(
        self, snapshot, fixt_auth_context, fixt_auth_dir
    ):  # noqa
        query = """mutation {updateAuthDir(
                      id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"
                      directory_url: "ldap://127.0.0.1"
                    ) {ok, auth_dir{status}}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_auth_dir_edit_bad_pass(
        self, snapshot, fixt_auth_context, fixt_auth_dir
    ):  # noqa
        query = """mutation {updateAuthDir(
                      id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"
                      service_username: "tst"
                    ) {ok, auth_dir{status}}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)


@pytest.mark.usefixtures("fixt_db")
class TestAuthenticationDirectoryMappings:
    """Проверки мэппингов."""

    async def test_add_auth_dir_mapp(
        self, snapshot, fixt_auth_context, fixt_group, fixt_auth_dir
    ):  # noqa
        query = """mutation {
                        addAuthDirMapping(
                            id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"
                            verbose_name: "test_mapping2"
                            value_type: OU
                            values: ["test", "test2"]
                            priority: 5000
                            description: "test mapping description"
                            groups: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"]) {
                            ok,
                            auth_dir{
                              id
                              mappings{
                                verbose_name
                              }
                            }
                          }
                        }"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        await Mapping.delete.gino.status()

    async def test_edit_auth_dir_mapp(
        self, snapshot, fixt_auth_context, fixt_auth_dir, fixt_group, fixt_mapping
    ):  # noqa
        query = """mutation {
                      editAuthDirMapping(
                        id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                        verbose_name: "editted mapping",
                        mapping_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"
                        groups: ["10913d5d-ba7a-4049-88c5-769267a6cbe4"]
                      ) {
                        ok
                        auth_dir {
                          id
                          mappings {
                            id
                            verbose_name
                            assigned_groups{
                              id
                            }
                            possible_groups{
                              id
                            }
                          }
                        }
                      }
                    }"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_del_auth_dir_mapp(
        self, snapshot, fixt_auth_context, fixt_auth_dir, fixt_group, fixt_mapping
    ):  # noqa
        query = """mutation {
                      deleteAuthDirMapping(
                        id: "10913d5d-ba7a-4049-88c5-769267a6cbe4",
                        mapping_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"
                      ) {
                        ok
                        auth_dir {
                          id
                          mappings {
                            id
                            verbose_name
                            assigned_groups{
                              id
                            }
                            possible_groups{
                              id
                            }
                          }
                        }
                      }
                    }"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)


@pytest.mark.usefixtures("fixt_db")
class TestAuthenticationDirectoryUtils:
    async def test_auth_dir_check(
        self, snapshot, fixt_auth_context, fixt_auth_dir
    ):  # noqa
        """Проверка соединения без пароля (не требует авторизации в MS Active Directory)."""
        query = """mutation{
                        testAuthDir(id: "10913d5d-ba7a-4049-88c5-769267a6cbe4")
                    {ok, auth_dir{status}}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_auth_dir_with_pass_check(
        self, snapshot, fixt_auth_context, fixt_auth_dir_with_pass
    ):  # noqa
        """Проверка соединения с паролем (требует авторизации в MS Active Directory)."""
        query = """mutation{
                                testAuthDir(id: "10913d5d-ba7a-4049-88c5-769267a6cbe5")
                            {ok, auth_dir{status}}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_auth_dir_with_bad_pass_check(
        self, snapshot, fixt_auth_context, fixt_auth_dir_with_pass_bad
    ):  # noqa
        """Проверка соединения с неправильным паролем (требует авторизации в MS Active Directory)."""
        query = """mutation{
                            testAuthDir(id: "10913d5d-ba7a-4049-88c5-769267a6cbe6")
                            {ok, auth_dir{status}}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)

    async def test_ipa_sync_new_only_group(
        self, snapshot, fixt_auth_context, fixt_ipa_with_pass
    ):  # noqa
        """Должна создаться новая группа без пользователей."""
        query = """mutation{syncAuthDirGroupUsers(
                    auth_dir_id: "10923d5d-ba7a-4049-88c5-769267a6cbe5",
                    sync_data:
                        {group_ad_guid: "66e4c554-652a-11eb-aee9-02fff06b60b5",
                         group_verbose_name: "ipausers",
                         group_ad_cn: "cn=ipausers,cn=groups,cn=accounts,dc=bazalt,dc=auth"})
                    {ok}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        group = await Group.query.where(
            Group.ad_guid == "66e4c554-652a-11eb-aee9-02fff06b60b5"
        ).gino.first()
        assert group
        await group.delete()

    async def test_auth_dir_sync_new_only_group_2(
        self, fixt_auth_context, fixt_redis_client, fixt_auth_dir_with_pass, fixt_local_group
    ):  # noqa
        """Должна создаться новая группа без пользователей."""
        query = """mutation{syncAuthDirGroupUsers(
                    auth_dir_id: "10913d5d-ba7a-4049-88c5-769267a6cbe5",
                    sync_data:
                        {group_ad_guid: "df4745bd-6a47-47bf-b5c7-43cf7e266067",
                         group_verbose_name: "test_group_2",
                         group_ad_cn: ""})
                    {ok}}"""
        try:
            await execute_scheme(auth_dir_schema, query, context=fixt_auth_context)
        except Exception as ex_msg:
            assert "В группе не найдены пользователи для синхронизации" in str(ex_msg)
        #else:
        #    raise AssertionError()

    async def test_auth_dir_sync_group_and_users(
        self, snapshot, fixt_auth_context, fixt_redis_client, fixt_auth_dir_with_pass
    ):  # noqa
        """Должна создаться новая группа и пользователи из AD."""
        query = """mutation{syncAuthDirGroupUsers(
                           auth_dir_id: "10913d5d-ba7a-4049-88c5-769267a6cbe5",
                           sync_data:
                               {group_ad_guid: "ec0efca9-5878-4ab4-bb8f-149af659e115",
                                group_verbose_name: "veil-ad-users",
                                group_ad_cn: "CN=veil-ad-users,CN=Users,DC=bazalt,DC=local"},
                                convert_local_users_to_ad: true)
                           {ok}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        # Проверяем что группа создалась
        group = await Group.query.where(
            Group.ad_guid == "ec0efca9-5878-4ab4-bb8f-149af659e115"
        ).gino.first()
        assert group
        # Проверяем что пользователь создался
        user = await User.query.where(User.username == "ad180").gino.first()
        assert user
        # Проверяем что пользователь в группе
        user_groups = await user.assigned_groups
        assert user_groups
        assert isinstance(user_groups, list)
        assert group.id == user_groups[0].id
        # Чистим
        await User.delete.where(User.username != "vdiadmin").gino.status()
        await group.delete()

    async def test_ipa_sync_group_and_users(
        self, snapshot, fixt_auth_context, fixt_redis_client, fixt_ipa_with_pass
    ):  # noqa
        """Должна создаться новая группа и пользователи из AD."""
        query = """mutation{syncAuthDirGroupUsers(
                           auth_dir_id: "10923d5d-ba7a-4049-88c5-769267a6cbe5",
                           sync_data:
                               {group_ad_guid: "66e4c554-652a-11eb-aee9-02fff06b60b5",
                                group_verbose_name: "ipausers",
                                group_ad_cn: "cn=ipausers,cn=groups,cn=accounts,dc=bazalt,dc=auth"})
                           {ok}}"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        # Проверяем что группа создалась
        group = await Group.query.where(
            Group.ad_guid == "66e4c554-652a-11eb-aee9-02fff06b60b5"
        ).gino.first()
        assert group
        # Проверяем что пользователь создался
        user = await User.query.where(User.username == "ad120").gino.first()
        assert user
        # Проверяем что пользователь в группе
        user_groups = await user.assigned_groups
        assert user_groups
        assert isinstance(user_groups, list)
        assert group.id == user_groups[0].id
        # Чистим
        await User.delete.where(User.username != "vdiadmin").gino.status()
        await group.delete()

    async def test_auth_dir_sync_possible_openldap_users(
        self, snapshot, fixt_auth_context, fixt_openldap_with_pass
    ):  # noqa
        """Проверяем что работает поиск по id и просмотр доступных для назначения групп."""
        query = """mutation{syncOpenLDAPUsers(
                                   auth_dir_id: "10923d5d-ba7a-4049-88c5-769267a6cbe7",
                                   ou: "users",
                                   convert_local_users_to_ad: true)
                                   {ok}
                }"""
        executed = await execute_scheme(
            auth_dir_schema, query, context=fixt_auth_context
        )
        snapshot.assert_match(executed)
        # Чистим
        await User.delete.where(User.username != "vdiadmin").gino.status()
