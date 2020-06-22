# -*- coding: utf-8 -*-
import pytest

from tornado.testing import gen_test

from tests.utils import execute_scheme, VdiHttpTestCase
from tests.fixtures import fixt_db, fixt_auth_context, fixt_user, fixt_user_admin, fixt_controller, fixt_create_static_pool, fixt_create_automated_pool, fixt_vm  # noqa

from vm.schema import vm_schema
from vm.models import Vm
from pool.models import Pool
from controller.models import Controller


pytestmark = [pytest.mark.vms]


@pytest.mark.asyncio
async def test_request_vms(fixt_db, fixt_auth_context):  # noqa
    qu = """
    {
        vms(ordering: "verbose_name"){
        verbose_name
        id
        template{
          verbose_name
        }
        management_ip
        status
        controller {
          address
        }
    }
    }
    """
    executed = await execute_scheme(vm_schema, qu, context=fixt_auth_context)  # noqa


@pytest.mark.asyncio
async def test_request_templates(fixt_db, fixt_auth_context):  # noqa
    qu = """
    {
        templates{
            verbose_name
            controller{
              address
            }
        }
    }
    """
    executed = await execute_scheme(vm_schema, qu, context=fixt_auth_context)  # noqa


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
        # TODO: тест выглядит странно из-за особенностей существующей фикстуры пула. Переработать на спринте тех.долга

        # Проверяем, исходное количество пользователей на фикстурной VM
        current_user = await self.get_test_vm_username()
        assert current_user is None

        # Закрепляем VM за пользователем
        query = """mutation{
                         assignVmToUser(vm_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4", username: "test_user")
                         {ok, vm{user{username}}}}"""

        executed = await execute_scheme(vm_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

        # Дополнительная проверка пользователя в БД.
        current_user = await self.get_test_vm_username()
        assert current_user == 'test_user'

        # Открепляем VM от всех пользователей.
        query = """mutation{
                         freeVmFromUser(vm_id: "10913d5d-ba7a-4049-88c5-769267a6cbe4"){ok}}"""

        executed = await execute_scheme(vm_schema, query, context=fixt_auth_context)
        snapshot.assert_match(executed)

        # Проверяем, исходное количество пользователей на фикстурной VM
        current_user = await self.get_test_vm_username()
        assert current_user is None


@pytest.mark.asyncio
@pytest.mark.usefixtures('fixt_db', 'fixt_controller', 'fixt_user_admin', 'fixt_create_static_pool')
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
        response_dict = yield self.get_response(**moking_dict)
        response_data = response_dict['data']
        self.assertEqual(response_data, 'success')

    @gen_test
    def test_bad_action(self):
        action = 'upstart'  # Заведомо неправильное действие.
        moking_dict = yield self.get_moking_dict(action=action)
        self.assertIsInstance(moking_dict, dict)
        response_dict = yield self.get_response(**moking_dict)
        response_error = response_dict['errors'][0]['message']
        expected_error = 'Параметр action значения {} неверный'.format(action)
        self.assertIn(expected_error, response_error)


@pytest.mark.asyncio
async def test_templates_and_sorting(fixt_db, fixt_controller, fixt_user_admin, fixt_create_automated_pool, fixt_auth_context):  # noqa

    # Получаем pool_id из динамической фикстуры пула
    pool_id = await Pool.select('id').gino.scalar()
    pool = await Pool.get(pool_id)

    # Получаем виртуальную машину из динамической фикстуры пула
    vm = await Vm.query.where(pool_id == pool_id).gino.first()

    # Получаем контроллер
    controller_id = await Controller.select('id').gino.scalar()
    controller = await Controller.get(controller_id)

    # Закрепляем VM за суперпользователем
    query = """mutation{
                     assignVmToUser(vm_id: "%s", username: "test_user_admin")
                     {ok, vm{user{username}}}}""" % vm.id
    executed = await execute_scheme(vm_schema, query, context=fixt_auth_context)  # noqa

    query = """{
                  templates(node_id: "%s", ordering: "verbose_name"){
                    verbose_name
                  }
                }""" % pool.node_id
    executed = await execute_scheme(vm_schema, query, context=fixt_auth_context)  # noqa

    query = """{
                  templates(controller_ip: "%s", ordering: "verbose_name"){
                    verbose_name
                  }
                }""" % controller.address
    executed = await execute_scheme(vm_schema, query, context=fixt_auth_context)  # noqa

    query = """{
                  templates(controller_ip: "%s", ordering: "controller"){
                    verbose_name
                  }
                }""" % controller.address
    executed = await execute_scheme(vm_schema, query, context=fixt_auth_context)  # noqa

    list = ["node", "template", "status"]
    for ordering in list:
        query = """{
                      vms(controller_ip: "%s", node_id: "%s",
                            get_vms_in_pools: false, ordering: "%s"){
                        verbose_name
                        id
                        template{
                          verbose_name
                        }
                        status
                        controller {
                          address
                        }
                    }
                    }""" % (controller.address, pool.node_id, ordering)
        executed = await execute_scheme(vm_schema, query, context=fixt_auth_context)  # noqa