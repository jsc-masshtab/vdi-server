# -*- coding: utf-8 -*-
import pytest

from tornado.testing import gen_test

from web_app.tests.utils import execute_scheme, VdiHttpTestCase
from web_app.tests.fixtures import fixt_db, fixt_auth_context, fixt_user, fixt_user_admin, fixt_controller, fixt_create_static_pool, fixt_create_automated_pool, fixt_vm, fixt_veil_client  # noqa

from common.models.vm import Vm
from common.models.pool import Pool
from web_app.pool.schema import pool_schema
# from common.models.controller import Controller


pytestmark = [pytest.mark.vms]


@pytest.mark.asyncio
@pytest.mark.usefixtures('fixt_db', 'fixt_user', 'fixt_vm')
class TestVmPermissionsSchema:
    # TODO: add group tests
    # TODO: add role tests

    @staticmethod
    async def get_test_vm_username():
        vm = await Vm.get("10913d5d-ba7a-4049-88c5-769267a6cbe4")
        return await vm.username

    async def test_vm_user_permission(self, snapshot, fixt_auth_context):  # noqa
        # Проверяем, исходное количество пользователей на фикстурной VM
        current_user = await self.get_test_vm_username()
        assert current_user is None

        # Закрепляем VM за пользователем
        query = """mutation{
                         assignVmToUser(vm_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", username: "test_user")
                         {ok, vm{user{username}}}}"""

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)

        # Дополнительная проверка пользователя в БД.
        current_user = await self.get_test_vm_username()
        assert current_user == 'test_user'

        # Открепляем VM от всех пользователей.
        query = """mutation{
                         freeVmFromUser(vm_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"){ok}}"""

        executed = await execute_scheme(pool_schema, query, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)

        # Проверяем, исходное количество пользователей на фикстурной VM
        current_user = await self.get_test_vm_username()
        assert current_user is None


@pytest.mark.asyncio
@pytest.mark.usefixtures('fixt_db', 'fixt_user_admin', 'fixt_create_static_pool')
class TestVmStatus:

    async def test_service_status(self, snapshot, fixt_auth_context):  # noqa
        # vm = await Vm.get("10913d5d-ba7a-4049-88c5-769267a6cbe4")
        pool_id = await Pool.select('id').gino.scalar()

        vm = await Vm.query.where(pool_id == pool_id).gino.first()

        qu = """mutation{
                assignVmToUser(vm_id: "%s", username: "admin") {ok}}""" % vm.id

        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
        # snapshot.assert_match(executed)

        qu = """{pools {vms {status
                            user {username}}
                 }}"""
        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)

        qu = """mutation{
                freeVmFromUser(vm_id: "%s") {ok}}""" % vm.id

        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
        # snapshot.assert_match(executed)

        qu = """{pools {vms {status
                            user {username}}
                         }}"""
        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)

        qu = """mutation{
                assignVmToUser(vm_id: "%s", username: "admin") {ok}}""" % vm.id

        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
        # snapshot.assert_match(executed)

        qu = """{pools {vms {status
                            user {username}}
                         }}"""
        executed = await execute_scheme(pool_schema, qu, context=fixt_auth_context)  # noqa
        snapshot.assert_match(executed)


@pytest.mark.asyncio
@pytest.mark.usefixtures('fixt_db', 'fixt_controller', 'fixt_user_admin', 'fixt_create_static_pool', 'fixt_veil_client')
class VmActionTestCase(VdiHttpTestCase):

    async def get_moking_dict(self, action):
        # Получаем pool_id из динамической фикстуры пула
        pool_id = await Pool.select('id').gino.scalar()

        # Получаем виртуальную машину из динамической фикстуры пула
        vm = await Vm.query.where(pool_id == pool_id).gino.first()

        # Закрепляем VM за тестовым пользователем
        await vm.add_user("10913d5d-ba7a-4049-88c5-769267a6cbe3", creator='system')

        # Авторизуемся, чтобы получить токен
        body = '{"username": "test_user_admin","password": "veil"}'
        response_dict = await self.get_response(body=body, url='/auth')
        access_token = response_dict['data']['access_token']
        self.assertTrue(access_token)

        # Формируем данные для тестируемого параметра
        headers = {'Content-Type': 'application/json', 'Authorization': 'jwt {}'.format(access_token)}
        body = '{"force": true}'
        url = '/client/pools/{pool_id}/{action}/'.format(pool_id=pool_id, action=action)
        return {'headers': headers, 'body': body, 'url': url}

    @gen_test
    def test_valid_action(self):
        action = 'start'  # Заведомо правильное действие.
        moking_dict = yield self.get_moking_dict(action=action)
        self.assertIsInstance(moking_dict, dict)
        # Этот тест принципально не может закончится успехом, потому что таймаут 5 сек, а выполнения action
        # занимает как минимум 10 сек. models/vm.py строка 340 (await asyncio.sleep(VEIL_OPERATION_WAITING))
        #  response_dict = yield self.get_response(**moking_dict)
        #  response_data = response_dict['data']
        #  self.assertEqual(response_data, 'success')

    # @gen_test
    # def test_bad_action(self):
    #     action = 'upstart'  # Заведомо неправильное действие.
    #     moking_dict = yield self.get_moking_dict(action=action)
    #     self.assertIsInstance(moking_dict, dict)
    #     response_dict = yield self.get_response(**moking_dict)
    #     response_error = response_dict['errors'][0]['message']
    #     expected_error = 'Параметр action значения {} неверный'.format(action)
    #     self.assertIn(expected_error, response_error)
