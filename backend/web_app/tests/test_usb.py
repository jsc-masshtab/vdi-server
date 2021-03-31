# -*- coding: utf-8 -*-
import pytest
import json

from tornado.testing import gen_test

from common.models.vm import Vm
from common.models.pool import Pool

from web_app.tests.utils import VdiHttpTestCase
from web_app.tests.fixtures import (
    fixt_db,  # noqa: F401
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

pytestmark = [pytest.mark.asyncio, pytest.mark.vms, pytest.mark.skipif(PAM_AUTH, reason="not finished yet")]


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

        headers = await self.generate_headers_for_tk()
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
