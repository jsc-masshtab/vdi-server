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
                         freeVmFromUser(vm_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", 
                                        username: "test_user"){ok}}"""

        executed = await execute_scheme(
            pool_schema, query, context=fixt_auth_context
        )  # noqa
        snapshot.assert_match(executed)

        # Проверяем, исходное количество пользователей на фикстурной VM
        current_user = await self.get_test_vm_username()
        assert current_user is None

        # Проверяем, количество свободных ВМ в пуле
        count_vm = await pool_obj.get_vm_amount(only_free=True)
        assert count_vm == 2


@pytest.mark.asyncio
@pytest.mark.usefixtures("fixt_db", "fixt_user_admin", "fixt_create_static_pool")
class TestVmStatus:
    async def test_reserved_status(self, snapshot, fixt_auth_context):  # noqa
        # vm = await Vm.get("10913d5d-ba7a-4049-88c5-769267a6cbe4")
        pool_id = await Pool.select("id").gino.scalar()

        vm = await Vm.query.where(pool_id == pool_id).gino.first()

        qu = (
            """mutation{
                reserveVm(vm_id: "%s", reserve: true) {ok}}"""
            % vm.id
        )

        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
        assert executed["reserveVm"]["ok"]

        qu = """{pools {vms {status}
                 }}"""
        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
        snapshot.assert_match(executed)

        qu = (
            """mutation{
                reserveVm(vm_id: "%s", reserve: false) {ok}}"""
            % vm.id
        )

        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
        assert executed["reserveVm"]["ok"]

        qu = """{pools {vms {status}
                         }}"""
        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
        snapshot.assert_match(executed)


@pytest.mark.asyncio
@pytest.mark.usefixtures("fixt_db", "fixt_user_admin", "fixt_create_static_pool")
class TestResolveVm:
    async def test_vm_info(self, snapshot, fixt_auth_context):  # noqa
        pool_id = await Pool.select("id").gino.scalar()
        pool = await Pool.get(pool_id)

        vm = await Vm.query.where(pool_id == pool_id).gino.first()

        qu = (
            """{pools{
                    vm (vm_id: "%s", controller_id: "%s") {
                       verbose_name
                    }
                } 
               }"""
            % (vm.id, pool.controller)
        )

        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)
        snapshot.assert_match(executed)


@pytest.mark.asyncio
@pytest.mark.usefixtures("fixt_db", "fixt_user_admin", "fixt_vm")
class TestFilterVm:
    async def test_get_vm_by_verbose_name(self):
        pool_id = await Pool.select("id").gino.scalar()
        pool = await Pool.get(pool_id)
        vms = await Pool.get_vms(pool, limit=None, offset=0, verbose_name="test_2")
        vm_names = [vm.verbose_name for vm in vms]
        assert "test_2" in vm_names

        # Проверка отсутствия ВМ с заданным verbose_name.
        vms = await Pool.get_vms(pool, limit=None, offset=0, verbose_name="vm_name")
        vm_names = [vm.verbose_name for vm in vms]
        assert len(vm_names) == 0
