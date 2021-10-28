# -*- coding: utf-8 -*-

from common.languages import _local_
from common.utils import create_subprocess
from common.veil.auth.veil_jwt import jwtauth
from common.veil.veil_handlers import BaseHttpHandler


@jwtauth
class GetStatisticsReport(BaseHttpHandler):
    """Обновляет статистику, создает отчет в виде html и возвращает его."""

    async def get(self):

        month = self.get_query_argument(name="month", default="all")
        year = self.get_query_argument(name="year", default="all")

        # Generate report
        cmd = "timeout 50s perl " \
              "/usr/local/awstats/wwwroot/cgi-bin/awstats.pl " \
              "-config=vdi -update -output -staticlinks -month={} -year={}".format(month, year)
        _, stdout, stderr = await create_subprocess(cmd)

        error_str = _local_("Failed to generate statistics report {}.")
        if stderr:
            response = self.form_err_res("{} {}.".format(error_str, stderr.decode()))
            return await self.log_finish(response)

        if not stdout:
            response = self.form_err_res(error_str)
            return await self.log_finish(response)

        report_html = stdout.decode()

        # Send response
        self.set_header("Content-Type", "text/html; charset=utf-8")
        return await self.log_finish(report_html)
