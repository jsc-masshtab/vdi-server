# -*- coding: utf-8 -*-

import graphene

from common.languages import _local_
from common.utils import create_subprocess
from common.veil.veil_errors import SimpleError


class StatisticsQuery(graphene.ObjectType):
    web_statistics_report = graphene.String(month=graphene.Int(), year=graphene.Int())

    async def resolve_web_statistics_report(
        self,
        _info,
        month=None,
        year=None,
        **kwargs
    ):
        # Generate report
        if month is None:
            month = "all"
        if year is None:
            year = "all"

        report_html = await StatisticsQuery.get_web_statistics_page(month, year)
        return report_html

    @staticmethod
    async def get_web_statistics_page(month, year):
        """Обновляет статистику, создает отчет в виде html и возвращает его."""
        cmd = "timeout 50s perl " \
              "/usr/lib/cgi-bin/awstats.pl " \
              "-config=vdi -update -output -staticlinks -month={} -year={}".format(month, year)
        _, stdout, stderr = await create_subprocess(cmd)

        base_error_str = _local_("Failed to generate statistics report.")
        if stderr:
            message = "{} {}.".format(base_error_str, stderr.decode())
            raise SimpleError(message)

        if not stdout:
            raise SimpleError(base_error_str)

        report_html = stdout.decode()
        return report_html


statistics_schema = graphene.Schema(
    query=StatisticsQuery, auto_camelcase=False
)
