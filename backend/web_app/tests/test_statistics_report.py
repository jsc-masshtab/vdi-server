# -*- coding: utf-8 -*-
import pytest
from tornado.testing import gen_test
from web_app.tests.utils import VdiHttpTestCase
from web_app.tests.fixtures import fixt_db, fixt_redis_client, fixt_user_admin  # noqa
from common.settings import PAM_AUTH

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(PAM_AUTH, reason="not finished yet"),
]


class StatisticsReportTestCase(VdiHttpTestCase):
    @pytest.mark.usefixtures("fixt_db", "fixt_user_admin")
    @gen_test
    async def test_get_statistics_report(self):

        auth_headers = await self.do_login_and_get_auth_headers(username="test_user_admin")

        response = await self.fetch_request(
            body=None, url="/statistics_report?month=all&year=all", headers=auth_headers, method="GET"
        )
        self.assertEqual(response.code, 200)
