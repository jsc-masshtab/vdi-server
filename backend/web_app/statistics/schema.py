# -*- coding: utf-8 -*-

import graphene

from sqlalchemy import and_, desc

from common.database import db
from common.graphene_utils import ShortString
from common.languages import _local_
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from common.models.pool import Pool
from common.models.tk_vm_connection import TkVmConnection
from common.models.vm import Vm
from common.utils import create_subprocess
from common.veil.veil_errors import SimpleError


class UsageData(graphene.ObjectType):
    name = ShortString()
    conn_number = graphene.Int()


class TimeIntervalData(graphene.ObjectType):
    time_interval = ShortString()
    conn_number = graphene.Int()
    percentage = graphene.Int()


class PoolUsageStatsType(graphene.ObjectType):

    def __init__(self, start_date, end_date, pool_id=None, **kwargs):
        super().__init__(**kwargs)
        self._start_date = start_date
        self._end_date = end_date
        self._pool_id = pool_id
        self._common_filters = PoolUsageStatsType.build_common_filters(TkVmConnection.connected_to_vm,
                                                                       self._start_date, self._end_date, pool_id)

    successful_conn_number = graphene.Int()
    disconn_number = graphene.Int()
    conn_err_number = graphene.Int()
    conn_duration_average = ShortString()

    used_pools_overall = graphene.List(UsageData, limit=graphene.Int(default_value=10),
                                       offset=graphene.Int(default_value=0))
    used_client_os = graphene.List(UsageData, limit=graphene.Int(default_value=10),
                                   offset=graphene.Int(default_value=0))
    used_client_versions = graphene.List(UsageData, limit=graphene.Int(default_value=10),
                                         offset=graphene.Int(default_value=0))
    users = graphene.List(UsageData, limit=graphene.Int(default_value=10),
                          offset=graphene.Int(default_value=0))

    conn_errors = graphene.List(UsageData, limit=graphene.Int(default_value=10),
                                offset=graphene.Int(default_value=0))

    conn_number_by_time_interval = graphene.List(TimeIntervalData)

    async def resolve_successful_conn_number(self, _info, **kwargs):

        successful_conn_number = (
            await db.select([db.func.count()]).select_from(TkVmConnection.join(Vm, TkVmConnection.vm_id == Vm.id)
                                                           .join(Pool, Pool.id == Vm.pool_id))
                .where((TkVmConnection.connected_to_vm != None) &  # noqa
                       TkVmConnection.successful & and_(*self._common_filters))  # noqa
                .gino.scalar()
        )
        return successful_conn_number

    async def resolve_disconn_number(self, _info, **kwargs):

        filters = PoolUsageStatsType.build_common_filters(TkVmConnection.disconnected_from_vm,
                                                          self._start_date, self._end_date, self._pool_id)
        disconn_number = await db.select([db.func.count()])\
            .select_from(TkVmConnection.join(Vm, TkVmConnection.vm_id == Vm.id)
                         .join(Pool, Pool.id == Vm.pool_id))\
            .where((TkVmConnection.disconnected_from_vm != None) &  # noqa
                   TkVmConnection.successful & and_(*filters))\
            .gino.scalar()

        return disconn_number

    async def resolve_conn_err_number(self, _info, **kwargs):

        conn_err_number = await db.select([db.func.count()])\
            .select_from(TkVmConnection.join(Vm, TkVmConnection.vm_id == Vm.id)
                         .join(Pool, Pool.id == Vm.pool_id))\
            .where((TkVmConnection.connected_to_vm != None) &  # noqa
                   (TkVmConnection.successful == False) & and_(*self._common_filters))\
            .gino.scalar()

        return conn_err_number

    async def resolve_conn_duration_average(self, _info, **kwargs):
        # duration_average. Для подключений к ВМ в заданом интервале
        conn_duration_average = await db.select(
            [db.func.avg(TkVmConnection.disconnected_from_vm - TkVmConnection.connected_to_vm)])\
            .select_from(TkVmConnection.join(Vm, TkVmConnection.vm_id == Vm.id)
                         .join(Pool, Pool.id == Vm.pool_id))\
            .where(TkVmConnection.successful
                   & (TkVmConnection.connected_to_vm != None)  # noqa
                   & (TkVmConnection.disconnected_from_vm != None)  # noqa
                   & and_(*self._common_filters)).gino.scalar()  # noqa

        return conn_duration_average

    async def resolve_used_pools_overall(self, _info, limit, offset, **kwargs):
        query = db.select([Pool.verbose_name, db.func.count()]).\
            select_from(Pool.join(Vm, Pool.id == Vm.pool_id).
                        join(TkVmConnection, Vm.id == TkVmConnection.vm_id))

        query = query.group_by(Pool.verbose_name)
        filters = PoolUsageStatsType.build_common_filters(TkVmConnection.connected_to_vm,
                                                          self._start_date, self._end_date)
        usage_data = await self.request_usage_data(query, limit, offset, filters)
        return usage_data

    async def resolve_used_client_os(self, _info, limit, offset, **kwargs):
        query = db.select([ActiveTkConnection.tk_os, db.func.count()]). \
            select_from(ActiveTkConnection.join(TkVmConnection)
                        .join(Vm, TkVmConnection.vm_id == Vm.id)
                        .join(Pool, Pool.id == Vm.pool_id))

        query = query.group_by(ActiveTkConnection.tk_os)
        usage_data = await self.request_usage_data(query, limit, offset, self._common_filters)
        return usage_data

    async def resolve_used_client_versions(self, _info, limit, offset, **kwargs):
        query = db.select([ActiveTkConnection.veil_connect_version, db.func.count()]). \
            select_from(ActiveTkConnection.join(TkVmConnection)
                        .join(Vm, TkVmConnection.vm_id == Vm.id)
                        .join(Pool, Pool.id == Vm.pool_id))

        query = query.group_by(ActiveTkConnection.veil_connect_version)
        usage_data = await self.request_usage_data(query, limit, offset, self._common_filters)
        return usage_data

    async def resolve_users(self, _info, limit, offset, **kwargs):
        query = db.select([User.username, db.func.count()]). \
            select_from(ActiveTkConnection.join(User, User.id == ActiveTkConnection.user_id, isouter=True)
                        .join(TkVmConnection, TkVmConnection.tk_connection_id == ActiveTkConnection.id)
                        .join(Vm, TkVmConnection.vm_id == Vm.id)
                        .join(Pool, Pool.id == Vm.pool_id))

        query = query.group_by(User.username)
        usage_data = await self.request_usage_data(query, limit, offset, self._common_filters)
        return usage_data

    async def resolve_conn_errors(self, _info, limit, offset, **kwargs):
        query = db.select([TkVmConnection.conn_error_str, db.func.count()]). \
            select_from(TkVmConnection.join(Vm, TkVmConnection.vm_id == Vm.id)
                        .join(Pool, Pool.id == Vm.pool_id))

        query = query.where(TkVmConnection.conn_error_str != None)  # noqa

        query = query.group_by(TkVmConnection.conn_error_str)
        usage_data = await self.request_usage_data(query, limit, offset, self._common_filters)
        return usage_data

    async def resolve_conn_number_by_time_interval(self, _info, **kwargs):
        """Возвращает количества подключений по интервалам дня."""
        # generate sql request. Из входных данных только временные лимиты self._start_date, self._end_date,
        # которые валидируются на уровне graphql
        hours_in_day = 24
        interval_query = ""
        for hour in range(hours_in_day):
            interval_query = "{},\nSUM(CASE WHEN connected_to_vm::time >= '{}:00' AND "\
                             "connected_to_vm::time < '{}:00' THEN 1 ELSE 0 end)".format(interval_query, hour, hour + 1)
        total_query = "SUM(CASE WHEN connected_to_vm::time >= '00:00' AND connected_to_vm::time < '23:59' " \
                      "THEN 1 ELSE 0 end)"
        main_time_limits = "connected_to_vm >= '{}' AND connected_to_vm < '{}'".format(
            self._start_date, self._end_date)

        if self._pool_id:
            final_request = """
                SELECT {} AS total{}
                FROM tk_vm_connection
                FULL OUTER JOIN vm
                ON tk_vm_connection.vm_id = vm.id
                FULL OUTER JOIN pool
                ON vm.pool_id = pool.id
                WHERE pool.id = '{}' AND {}
                """.format(total_query, interval_query, str(self._pool_id), main_time_limits)
        else:
            final_request = """
                  SELECT {} AS total{}
                  FROM tk_vm_connection
                  WHERE {}
                  """.format(total_query, interval_query, main_time_limits)

        query = db.text(final_request)
        conn_data_by_time_intervals = await db.all(query)
        conn_data_by_time_intervals = list(*conn_data_by_time_intervals)
        all_conn_number = conn_data_by_time_intervals[0]

        conn_by_time_intervals = []
        for hour in range(hours_in_day):
            time_interval = "{:02d}:00-{:02d}:00".format(hour, hour + 1)
            conn_number = conn_data_by_time_intervals[hour + 1]
            if all_conn_number and conn_number:
                percentage = round(float(conn_number) / float(all_conn_number) * 100)
                conn_by_time_intervals.append(TimeIntervalData(time_interval=time_interval,
                                                               conn_number=conn_number,
                                                               percentage=percentage))
            else:
                conn_by_time_intervals.append(TimeIntervalData(time_interval=time_interval,
                                                               conn_number=0,
                                                               percentage=0))

        return conn_by_time_intervals

    async def request_usage_data(self, query, limit, offset, filters):
        query = query.where(and_(*filters))

        query = query.order_by(desc(db.func.count()))

        usage_data = await query.limit(limit).offset(offset).gino.all()
        usage_data = [UsageData(name=name, conn_number=conn_number) for (name, conn_number) in usage_data]
        return usage_data

    @staticmethod
    def build_common_filters(date_field, start_date, end_date, pool_id=None):
        filters = []
        if start_date:
            filters.append((date_field >= start_date))
        if end_date:
            filters.append((date_field <= end_date))
        if pool_id:
            filters.append((Pool.id == pool_id))

        return filters


class StatisticsQuery(graphene.ObjectType):
    web_statistics_report = graphene.String(month=graphene.Int(), year=graphene.Int())

    pool_usage_statistics = graphene.Field(PoolUsageStatsType,
                                           start_date=graphene.DateTime(),
                                           end_date=graphene.DateTime(),
                                           pool_id=graphene.UUID())

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

    async def resolve_pool_usage_statistics(self, _info, start_date, end_date, pool_id=None, **kwargs):

        if pool_id:
            pool = await Pool.get(pool_id)
            if not pool:
                raise SimpleError(_local_("Pool with id {} does not exist.").format(pool_id))

        pool_usage_statistics = PoolUsageStatsType(start_date, end_date, pool_id)
        return pool_usage_statistics

    @staticmethod
    async def get_web_statistics_page(month, year):
        """Обновляет статистику, создает отчет в виде html и возвращает его."""
        cmd = "/usr/sbin/vdi_update_web_statistics.sh {} {}".format(month, year)
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
