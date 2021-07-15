# -*- coding: utf-8 -*-
import pytest
import json
import asyncio
from uuid import uuid4
from common.database import db

import tornado
from tornado.testing import gen_test

from web_app.tests.utils import VdiHttpTestCase

from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from common.models.pool import Pool
from common.models.vm import Vm
from common.models.user_tk_permission import TkPermission

from web_app.tests.utils import execute_scheme
from web_app.thin_client_api.schema import thin_client_schema
from common.settings import PAM_AUTH
from web_app.tests.fixtures import (
    fixt_db,  # noqa: F401
    fixt_redis_client,
    fixt_user_locked,  # noqa: F401
    fixt_user,  # noqa: F401
    fixt_user_admin,  # noqa: F401
    fixt_auth_dir,  # noqa: F401
    fixt_mapping,  # noqa: F401
    fixt_group,  # noqa: F401
    fixt_group_role,  # noqa: F401
    fixt_create_static_pool,  # noqa: F401
    fixt_controller,  # noqa: F401
    fixt_veil_client,  # noqa: F401
    get_auth_context,  # noqa: F401
    several_static_pools,  # noqa: F401
    several_static_pools_with_user,  # noqa: F401
)

from common.subscription_sources import WsMessageType


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.ws_requests,
    pytest.mark.tk,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


class TestWebsockets(VdiHttpTestCase):

    @pytest.mark.usefixtures("fixt_db", "fixt_user_admin")
    @gen_test
    async def test_ws_connect_update_disconnect_ok(self):
        """Check ws communication"""
        # clear all
        await db.status(db.text('TRUNCATE TABLE active_tk_connection CASCADE;'))

        # login
        (user_name, access_token) = await self.do_login()

        # connect to ws
        ws_url = (
            "ws://localhost:" + str(self.get_http_port()) + "/ws/client?token={}"
            "&is_conn_init_by_user=0"
            "&veil_connect_version=1.4.1"
            "&tk_os=Linux".format(access_token)
        )
        ws_client = await tornado.websocket.websocket_connect(ws_url)
        assert ws_client

        try:
            # update (Эмулировать подключение к ВМ)
            vm_id = "201d318f-d57e-4f1b-9097-93d69f8782dd"
            update_data_dict = {
                "msg_type": WsMessageType.UPDATED.value,
                "vm_id": vm_id,
                "event": "vm_changed",
            }
            ws_client.write_message(json.dumps(update_data_dict))
            await asyncio.sleep(1)  # Подождем так как на update ответов не присылается

            user_id = await User.get_id(user_name)
            real_vm_id = (
                await ActiveTkConnection.select("vm_id")
                .where(ActiveTkConnection.user_id == user_id)
                .gino.scalar()
            )
            self.assertEqual(vm_id, str(real_vm_id))

            # test current connection data
            qu = """{
                    thin_clients_count
                }"""
            auth_context = await get_auth_context()
            executed = await execute_scheme(
                thin_client_schema, qu, context=auth_context
            )
            assert executed["thin_clients_count"] == 1
            # Получаем последнее подключение для юзера user_id
            qu = (
                """{
                        thin_clients(offset:0, limit: 1, ordering: "connected", user_id: "%s"){
                          conn_id
                          user_name
                          veil_connect_version
                          vm_name
                          tk_ip
                          tk_os
                          connected
                          data_received
                      }
                  }"""
                % user_id
            )
            auth_context = await get_auth_context()
            executed = await execute_scheme(
                thin_client_schema, qu, context=auth_context
            )
            assert len(executed["thin_clients"]) == 1
            assert executed["thin_clients"][0]["user_name"] == user_name
            conn_id = executed["thin_clients"][0]["conn_id"]

            # update (Эмулировать отправку сетевой статистики с ТК)
            update_data_dict = {
                "msg_type": WsMessageType.UPDATED.value,
                "event": "network_stats",
                "connection_type": Pool.PoolConnectionTypes.RDP.name,
                "read_speed": 1024,
                "write_speed": 1024,
                "min_rtt": 3,
                "avg_rtt": 4,
                "max_rtt": 5,
                "loss_percentage": 0,
            }
            ws_client.write_message(json.dumps(update_data_dict))
            await asyncio.sleep(1)  # Подождем так как на update ответов не присылается

            # disconnect request
            qu = (
                """
                mutation{
                    disconnectThinClient(conn_id: "%s"){
                        ok
                    }
                }"""
                % conn_id
            )
            executed = await execute_scheme(thin_client_schema, qu,
                                            context=auth_context)
            assert executed["disconnectThinClient"]["ok"]

        except Exception:
            raise
        finally:
            # disconnect
            ws_client.close()
            await asyncio.sleep(0.1)


class TestPool(VdiHttpTestCase):

    API_URL = "/client/pools/"

    @pytest.mark.usefixtures("fixt_db", "fixt_user_admin", "fixt_create_static_pool")
    @gen_test
    async def test_superuser_pools_list(self):
        """Check tk rest api"""
        auth_headers = await self.get_auth_headers(username="test_user_admin")

        response_dict = await self.get_response(
            body=None, url=self.API_URL, headers=auth_headers, method="GET"
        )
        assert len(response_dict["data"]) == 1

    @pytest.mark.usefixtures("fixt_db", "fixt_user", "fixt_create_static_pool")
    @gen_test
    async def test_user_has_no_pools(self):
        """Сценарий, когда у пользователя нет закрепленных пулов."""
        auth_headers = await self.get_auth_headers(username="test_user")

        response_dict = await self.get_response(
            body=None, url=self.API_URL, headers=auth_headers, method="GET"
        )
        assert "data" in response_dict
        assert len(response_dict["data"]) == 0

    @pytest.mark.usefixtures("fixt_db", "fixt_user", "several_static_pools")
    @gen_test
    async def test_user_has_one_pool(self):
        """Сценарий, когда обычному пользователю выдан 1 пул из 2х."""
        # Данные для подключения
        auth_headers = await self.get_auth_headers(username="test_user")
        # Проверяем, что изначально нет пулов
        response_dict = await self.get_response(
            body=None, url=self.API_URL, headers=auth_headers, method="GET"
        )
        assert "data" in response_dict
        assert len(response_dict["data"]) == 0
        # Закрепляем 1 из пулов за пользователем
        pool = await Pool.query.gino.first()
        await pool.add_user("10913d5d-ba7a-4049-88c5-769267a6cbe4", "system")
        # Проверяем, что пользователю выдался пул
        response_dict = await self.get_response(
            body=None, url=self.API_URL, headers=auth_headers, method="GET"
        )
        assert "data" in response_dict
        assert len(response_dict["data"]) == 1


class TestPoolVm(VdiHttpTestCase):

    API_URL = "/client/pools/{pool_id}"

    @pytest.mark.usefixtures("fixt_db", "fixt_user", "several_static_pools_with_user")
    @gen_test(timeout=20)
    def test_bad_license(self):
        self.init_fake_license(expired=True)
        vm_url = self.API_URL.format(pool_id=str(uuid4()))
        body = ''
        auth_headers = yield self.get_auth_headers(username="test_user")
        response_dict = yield self.get_response(
            body=body, url=vm_url, headers=auth_headers, method="POST"
        )

        assert 'errors' in response_dict
        assert '001' == response_dict['errors'][0]['code']

    @pytest.mark.usefixtures("fixt_db", "fixt_user")
    @gen_test(timeout=20)
    def test_bad_pool_id(self):
        """Сценарий, когда отправляется несуществующий пул."""
        vm_url = self.API_URL.format(pool_id=str(uuid4()))
        body = ''
        auth_headers = yield self.get_auth_headers(username="test_user")
        response_dict = yield self.get_response(
            body=body,
            url=vm_url,
            headers=auth_headers,
        )

        assert 'errors' in response_dict
        assert '404' == response_dict['errors'][0]['code']

    @pytest.mark.usefixtures("fixt_db", "fixt_user", "several_static_pools_with_user")
    @gen_test(timeout=20)
    def test_user_get_vm(self):
        """Сценарий получения пользователем ВМ из пула."""
        pool = yield Pool.query.gino.first()
        get_vm_url = self.API_URL.format(pool_id=pool.id_str)
        auth_headers = yield self.get_auth_headers(username="test_user")
        body = ''
        # Получаем
        response_dict = yield self.get_response(
            body=body,
            url=get_vm_url,
            headers=auth_headers,
        )
        # Проверяем, что ВМ выдана
        assert 'data' in response_dict
        port = response_dict['data']['port']
        assert port == 5900
        # Проверка наличие всех разрешений
        permissions = response_dict['data']['permissions']
        for permission_type in TkPermission:
            assert permission_type.name in permissions

        pool_type = response_dict['data']['pool_type']
        assert pool_type == 'STATIC'
        host = response_dict['data']['host']
        assert host == '0.0.0.0'
        assert 'vm_id' in response_dict['data']
        vm_controller_address = response_dict['data']['vm_controller_address']
        assert vm_controller_address == '0.0.0.0'
        vm_verbose_name = response_dict['data']['vm_verbose_name']
        assert vm_verbose_name == 'alt_linux'
        password = response_dict['data']['password']
        assert password == '1'

    @pytest.mark.usefixtures("fixt_db", "fixt_user", "several_static_pools_with_user")
    @gen_test(timeout=20)
    def test_bad_connection_type(self):
        pool = yield Pool.query.gino.first()
        vm_url = self.API_URL.format(pool_id=pool.id_str)
        body = json.dumps({"remote_protocol": "BAD"})
        auth_headers = yield self.get_auth_headers(username="test_user")
        response_dict = yield self.get_response(
            body=body, url=vm_url, headers=auth_headers, method="POST"
        )

        assert 'errors' in response_dict
        assert '404' == response_dict['errors'][0]['code']

    @pytest.mark.usefixtures("fixt_db", "fixt_user", "several_static_pools_with_user")
    @gen_test(timeout=20)
    def test_rdp_connection_type(self):
        pool = yield Pool.query.gino.first()
        vm_url = self.API_URL.format(pool_id=pool.id_str)
        body = json.dumps({"remote_protocol": "RDP"})
        auth_headers = yield self.get_auth_headers(username="test_user")
        response_dict = yield self.get_response(
            body=body, url=vm_url, headers=auth_headers, method="POST"
        )
        # Проверяем, что ВМ выдана
        assert 'errors' in response_dict
        assert '005' == response_dict['errors'][0]['code']


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    "fixt_db",
    "fixt_controller",
    "fixt_user_admin",
    "fixt_create_static_pool",
    "fixt_veil_client",
)
class VmActionTestCase(VdiHttpTestCase):
    async def get_moking_dict(self, action):

        # Получаем pool_id из динамической фикстуры пула
        pool_id = await Pool.select("id").gino.scalar()

        # Получаем виртуальную машину из динамической фикстуры пула
        vm = await Vm.query.where(pool_id == pool_id).gino.first()

        # Закрепляем VM за тестовым пользователем
        await vm.add_user("10913d5d-ba7a-4049-88c5-769267a6cbe3", creator="system")

        # Формируем данные для тестируемого параметра
        headers = await self.get_auth_headers()
        body = '{"force": true}'
        url = "/client/pools/{pool_id}/{action}/".format(pool_id=pool_id, action=action)
        return {"headers": headers, "body": body, "url": url}

    @gen_test(timeout=20)
    async def test_valid_action(self):
        action = 'start'  # Заведомо правильное действие.
        moking_dict = await self.get_moking_dict(action=action)
        self.assertIsInstance(moking_dict, dict)
        response_dict = await self.get_response(**moking_dict)
        response_data = response_dict['data']
        self.assertEqual(response_data, 'success')


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    "fixt_db",
    "fixt_controller",
    "fixt_user_admin",
    "fixt_create_static_pool",
    "fixt_veil_client",
)
class USbTestCase(VdiHttpTestCase):

    @gen_test
    async def test_attach_detach_usb_ok(self):

        # Получаем pool_id из динамической фикстуры пула
        pool_id = await Pool.select("id").gino.scalar()

        # Получаем виртуальную машину из динамической фикстуры пула
        vm = await Vm.query.where(pool_id == pool_id).gino.first()

        # Закрепляем VM за тестовым пользователем
        await vm.add_user("10913d5d-ba7a-4049-88c5-769267a6cbe3", creator="system")

        headers = await self.get_auth_headers()
        # Формируем данные для attach usb запроса
        usb_tcp_port = 17001
        usb_tcp_ip = "127.0.0.1"
        send_data = dict(host_address=usb_tcp_ip, host_port=usb_tcp_port)
        body = json.dumps(send_data)

        url = "/client/pools/{pool_id}/attach-usb/".format(pool_id=pool_id)
        request_data_dict = {"headers": headers, "body": body, "url": url}

        # Send attach request
        response_dict = await self.get_response(**request_data_dict)
        # print('!!!response_dict ', response_dict, flush=True)
        usb_array = response_dict['tcp_usb_devices']

        # some attach response checks
        try:
            usb = next(usb for usb in usb_array if usb['service'] == usb_tcp_port and usb['host'] == usb_tcp_ip)
        except StopIteration:
            raise AssertionError("USB not found")

        usb_uuid = usb.get('uuid')
        assert usb_uuid is not None

        # Данные для detach
        send_data = dict(usb_uuid=usb_uuid, remove_all=False)
        body = json.dumps(send_data)

        url = "/client/pools/{pool_id}/detach-usb/".format(pool_id=pool_id)
        request_data_dict = {"headers": headers, "body": body, "url": url}

        # Send detach request
        await self.get_response(**request_data_dict)
