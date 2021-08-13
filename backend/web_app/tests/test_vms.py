# -*- coding: utf-8 -*-
import pytest
from tornado.testing import gen_test

from web_app.tests.utils import execute_scheme, VdiHttpTestCase
from web_app.tests.fixtures import (
    fixt_db,  # noqa: F401
    fixt_redis_client,
    fixt_auth_context,  # noqa: F401
    fixt_user,  # noqa: F401
    fixt_user_admin,  # noqa: F401
    fixt_controller,  # noqa: F401
    fixt_create_static_pool,  # noqa: F401
    fixt_create_automated_pool,  # noqa: F401
    fixt_vm,  # noqa: F401
    fixt_veil_client,  # noqa: F401
)  # noqa: F401
from common.settings import PAM_AUTH
from common.models.vm import Vm
from common.models.pool import Pool
from web_app.pool.schema import pool_schema


pytestmark = [pytest.mark.asyncio, pytest.mark.vms, pytest.mark.skipif(PAM_AUTH, reason="not finished yet")]


@pytest.mark.asyncio
@pytest.mark.usefixtures("fixt_db", "fixt_user", "fixt_vm")
class TestVmPermissionsSchema:

    @staticmethod
    async def get_test_vm_username():
        vm = await Vm.get("10913d5d-ba7a-4049-88c5-769267a6cbe4")
        return await vm.username

    async def test_vm_user_permission(self, snapshot, fixt_auth_context):  # noqa
        # Проверяем, исходное количество пользователей на VM
        current_user = await self.get_test_vm_username()
        assert current_user is None

        # Проверяем запрет использования пула пользователем без прав
        try:
            query = """mutation{
                                 assignVmToUser(vm_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", username: "test_user")
                                 {ok, vm{user{username}}}}"""

            await execute_scheme(pool_schema, query, context=fixt_auth_context)
        except Exception:
            assert True
        else:
            assert False

        # Разрешаем пользователю пользоваться пулом
        vm_obj = await Vm.get("10913d5d-ba7a-4049-88c5-769267a6cbe4")
        pool_obj = await Pool.get(vm_obj.pool_id)
        await pool_obj.add_user(
            user_id="10913d5d-ba7a-4049-88c5-769267a6cbe4", creator="system"
        )

        # Закрепляем VM за пользователем
        query = """mutation{
                         assignVmToUser(vm_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", username: "test_user")
                         {ok, vm{user{username}}}}"""

        executed = await execute_scheme(
            pool_schema, query, context=fixt_auth_context
        )  # noqa
        snapshot.assert_match(executed)

        # Дополнительная проверка пользователя в БД.
        current_user = await self.get_test_vm_username()
        assert current_user == "test_user"

        # Открепляем VM от всех пользователей.
        query = """mutation{
                         freeVmFromUser(vm_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"){ok}}"""

        executed = await execute_scheme(
            pool_schema, query, context=fixt_auth_context
        )  # noqa
        snapshot.assert_match(executed)

        # Проверяем, исходное количество пользователей на фикстурной VM
        current_user = await self.get_test_vm_username()
        assert current_user is None


@pytest.mark.asyncio
@pytest.mark.usefixtures("fixt_db", "fixt_user_admin", "fixt_create_static_pool")
class TestVmStatus:
    async def test_reserved_status(self, snapshot, fixt_auth_context):  # noqa
        # vm = await Vm.get("10913d5d-ba7a-4049-88c5-769267a6cbe4")
        pool_id = await Pool.select("id").gino.scalar()

        vm = await Vm.query.where(pool_id == pool_id).gino.first()

        qu = (
            """mutation{
                assignVmToUser(vm_id: "%s", username: "vdiadmin") {ok}}"""
            % vm.id
        )

        executed = await execute_scheme(
            pool_schema, qu, context=fixt_auth_context
        )  # noqa
        # snapshot.assert_match(executed)

        qu = """{pools {vms {status
                            user {username}}
                 }}"""
        executed = await execute_scheme(
            pool_schema, qu, context=fixt_auth_context
        )  # noqa
        snapshot.assert_match(executed)

        qu = (
            """mutation{
                freeVmFromUser(vm_id: "%s") {ok}}"""
            % vm.id
        )

        executed = await execute_scheme(
            pool_schema, qu, context=fixt_auth_context
        )  # noqa
        # snapshot.assert_match(executed)

        qu = """{pools {vms {status
                            user {username}}
                         }}"""
        executed = await execute_scheme(
            pool_schema, qu, context=fixt_auth_context
        )  # noqa
        snapshot.assert_match(executed)

        qu = (
            """mutation{
                assignVmToUser(vm_id: "%s", username: "vdiadmin") {ok}}"""
            % vm.id
        )

        executed = await execute_scheme(
            pool_schema, qu, context=fixt_auth_context
        )  # noqa
        # snapshot.assert_match(executed)

        qu = """{pools {vms {status
                            user {username}}
                         }}"""
        executed = await execute_scheme(
            pool_schema, qu, context=fixt_auth_context
        )  # noqa
        snapshot.assert_match(executed)
