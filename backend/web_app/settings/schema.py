# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import datetime, timezone
from enum import Enum

from dateutil.tz import tzlocal

import graphene

from common.graphene_utils import ShortString
from common.languages import _local_
from common.log.journal import system_logger
from common.models.settings import Settings
from common.utils import create_subprocess
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SilentError, SimpleError


# Dictionary of services.{Service name: human friendly service name}.
app_services = OrderedDict([
    # external services
    ("apache2.service", _local_("Apache server.")),
    ("postgresql.service", _local_("Database.")),
    ("postgresql@9.6-main.service", _local_("Database.")),
    ("redis-server.service", "Redis."),
    # app services
    ("vdi-monitor_worker.service", _local_("Monitor worker.")),
    ("vdi-pool_worker.service", _local_("Task worker.")),
    ("vdi-web.service", _local_("Web application.")),
])


class ServiceAction(Enum):
    """Действия над сервисами."""

    START = "start"
    STOP = "stop"
    RESTART = "restart"


ServiceActionGraphene = graphene.Enum.from_enum(ServiceAction)


class SettingsType(graphene.ObjectType):
    LANGUAGE = graphene.Field(ShortString)
    DEBUG = graphene.Boolean()
    VEIL_CACHE_TTL = graphene.Int()
    VEIL_CACHE_SERVER = graphene.Field(ShortString)
    VEIL_CACHE_PORT = graphene.Int()
    VEIL_REQUEST_TIMEOUT = graphene.Int()
    VEIL_CONNECTION_TIMEOUT = graphene.Int()
    VEIL_GUEST_AGENT_EXTRA_WAITING = graphene.Int()
    VEIL_OPERATION_WAITING = graphene.Int()
    VEIL_MAX_BODY_SIZE = graphene.Int()
    VEIL_MAX_CLIENTS = graphene.Int()
    VEIL_SSL_ON = graphene.Boolean()
    VEIL_WS_MAX_TIME_TO_WAIT = graphene.Int()
    VEIL_VM_PREPARE_TIMEOUT = graphene.Int()
    VEIL_MAX_URL_LEN = graphene.Int()
    VEIL_MAX_IDS_LEN = graphene.Int()
    VEIL_MAX_VM_CREATE_ATTEMPTS = graphene.Int()


class SmtpSettingsType(graphene.ObjectType):
    hostname = graphene.Field(ShortString)
    port = graphene.Int()
    TLS = graphene.Boolean()
    SSL = graphene.Boolean()
    password = graphene.Field(ShortString)
    user = graphene.Field(ShortString)
    from_address = graphene.Field(ShortString)
    level = graphene.Int()


class ServiceGrapheneType(graphene.ObjectType):
    service_name = graphene.Field(ShortString)
    verbose_name = graphene.Field(ShortString)
    status = graphene.Field(ShortString)


class NetworkGrapheneType(graphene.ObjectType):
    name = graphene.Field(ShortString)
    ipv4 = graphene.Field(ShortString)


class SysInfoGrapheneType(graphene.ObjectType):
    networks_list = graphene.List(NetworkGrapheneType)
    local_time = graphene.DateTime()
    time_zone = graphene.Field(ShortString)


class SettingsQuery(graphene.ObjectType):
    settings = graphene.Field(SettingsType)
    smtp_settings = graphene.Field(SmtpSettingsType)

    services = graphene.List(ServiceGrapheneType)

    system_info = graphene.Field(SysInfoGrapheneType)

    @administrator_required
    async def resolve_settings(self, _info, **kwargs):
        settings = await Settings.get_settings()
        settings_list = SettingsType(**settings)
        return settings_list

    @administrator_required
    async def resolve_smtp_settings(self, _info, **kwargs):
        smtp_settings = await Settings.get_smtp_settings()
        smtp_settings_list = SmtpSettingsType(**smtp_settings)
        return smtp_settings_list

    @administrator_required
    async def resolve_services(self, _info, creator):
        """Get app related services."""
        # Get info
        cmd = "timeout 50s systemctl list-units --no-pager --no-legend --type=service | awk '{print $1\":\"$4}'"
        _, stdout, stderr = await create_subprocess(cmd)

        if stderr:
            raise SimpleError(
                _local_("Unable to get services information. {}.").format(stderr.decode()),
                user=creator
            )
        if not stdout:
            raise SilentError(_local_("No services launched."))

        # Parse info
        stdout_str = stdout.decode()
        # print("stdout.decode()", stdout_str, flush=True)

        current_services = dict()
        for service_str in stdout_str.splitlines():
            try:
                service_name, service_status = service_str.split(":", 2)
                current_services[service_name] = service_status
            except (IndexError, TypeError, KeyError) as ex:
                raise SimpleError(
                    _local_("Output parsing error. {}.").format(str(ex)),
                    user=creator
                )

        # Form response
        service_graphene_type_list = []

        for service_name, verbose_name in app_services.items():
            # Пропускаем postgresql.service так как этот сервис в завершенном состоянии на астре
            # и его статус неинтересен пользователю
            if service_name == "postgresql.service":
                continue

            service_status = current_services.get(service_name, "stopped")
            service_graphene_type = ServiceGrapheneType(
                service_name=service_name,
                verbose_name=verbose_name,
                status=service_status)
            service_graphene_type_list.append(service_graphene_type)

        return service_graphene_type_list

    @administrator_required
    async def resolve_system_info(self, _info, creator):
        """Get some system information."""
        sys_info_graphene_type = SysInfoGrapheneType()

        # get network data
        cmd = "ip -o -4 a|awk '{print $2\":\"$4}' | cut -f1  -d'/'"
        _, stdout, stderr = await create_subprocess(cmd)

        if stderr:
            await system_logger.error(
                message="Error during ip addresses checking.",
                description=stderr.decode(),
                user=creator
            )

        if stdout:
            stdout_str = stdout.decode()
            networks_list = []
            for item_str in stdout_str.splitlines():
                try:
                    net_interface_name, ip_addr = item_str.split(":", 2)
                    if ip_addr.strip() == "127.0.0.1":
                        continue

                    network_graphene_type = NetworkGrapheneType()
                    network_graphene_type.name = net_interface_name
                    network_graphene_type.ipv4 = ip_addr

                    networks_list.append(network_graphene_type)

                except (IndexError, TypeError, KeyError) as ex:
                    await system_logger.error(
                        message="Error during ip addresses parsing.",
                        description=str(ex),
                        user=creator
                    )

            sys_info_graphene_type.networks_list = networks_list

        # get time related data
        sys_info_graphene_type.local_time = datetime.now(timezone.utc)
        tz_name = datetime.now(tzlocal()).tzname()
        tz_offset = datetime.now(tzlocal()).utcoffset()
        sys_info_graphene_type.time_zone = "{}  {}".format(tz_name, tz_offset)

        return sys_info_graphene_type


class ChangeSettingsMutation(graphene.Mutation):
    class Arguments:
        LANGUAGE = ShortString(description="Язык сообщений журнала")
        DEBUG = graphene.Boolean()
        VEIL_CACHE_TTL = graphene.Int()
        VEIL_CACHE_SERVER = ShortString()
        VEIL_CACHE_PORT = graphene.Int()
        VEIL_REQUEST_TIMEOUT = graphene.Int()
        VEIL_CONNECTION_TIMEOUT = graphene.Int()
        VEIL_GUEST_AGENT_EXTRA_WAITING = graphene.Int()
        VEIL_OPERATION_WAITING = graphene.Int()
        VEIL_MAX_BODY_SIZE = graphene.Int()
        VEIL_MAX_CLIENTS = graphene.Int()
        VEIL_SSL_ON = graphene.Boolean()
        VEIL_WS_MAX_TIME_TO_WAIT = graphene.Int()
        VEIL_VM_PREPARE_TIMEOUT = graphene.Int()
        VEIL_MAX_URL_LEN = graphene.Int()
        VEIL_MAX_IDS_LEN = graphene.Int()
        VEIL_MAX_VM_CREATE_ATTEMPTS = graphene.Int()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, creator, **kwargs):
        ok = await Settings.change_settings(creator=creator, **kwargs)
        return ChangeSettingsMutation(ok=ok)


class ChangeSmtpSettingsMutation(graphene.Mutation):
    class Arguments:
        hostname = ShortString()
        port = graphene.Int()
        TLS = graphene.Boolean()
        SSL = graphene.Boolean()
        password = ShortString()
        user = ShortString()
        from_address = ShortString()
        level = graphene.Int()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, creator, **kwargs):
        ok = await Settings.change_smtp_settings(creator=creator, **kwargs)
        return ChangeSmtpSettingsMutation(ok=ok)


class DoServiceAction(graphene.Mutation):
    class Arguments:
        service_name = ShortString()
        service_action = ServiceActionGraphene()
        check_errors = graphene.Boolean()
        sudo_password = ShortString()  # legacy. Remove later

    ok = graphene.Boolean()
    service_status = ShortString()

    @administrator_required
    async def mutate(self, _info, creator, service_name, service_action,
                     check_errors=True, sudo_password=None):

        if service_name not in app_services.keys():
            raise SimpleError(
                _local_("Invalid service name {}.").format(service_name),
                user=creator
            )

        # Do action
        # Особый случай для postgresql@9.6-main.service. Он находится под управлением postgresql.service и
        # именно с последним мы и выполняем действие
        if service_name == "postgresql@9.6-main.service":
            parent_service_name = "postgresql.service"
        else:
            parent_service_name = service_name
        cmd = "timeout 50s systemctl {} {}".format(service_action, parent_service_name)

        return_code, stdout, stderr = await create_subprocess(cmd)

        if check_errors and stderr:
            raise SimpleError(
                _local_("Error occurred during service action executing. {}.").format(stderr.decode()),
                description="Return code: {}".format(return_code),
                user=creator
            )

        await system_logger.info(_local_("Executed action {} for service {}.").
                                 format(service_action, service_name), user=creator)

        # Try to get status of the service.
        service_status = "stopped"
        try:
            cmd = """timeout 50s systemctl list-units --no-pager --no-legend --type=service"""\
                  """ | awk '{print $1\":\"$4}' | grep %s""" % service_name

            _, stdout, stderr = await create_subprocess(cmd)
            if stderr:
                raise RuntimeError(stderr.decode())
            if stdout:
                stdout_str = stdout.decode()
                _, service_status = stdout_str.split(":", 2)
                service_status = service_status.strip()

        except Exception as ex:
            await system_logger.debug(
                _local_("Unable to check status of service {}.").format(service_name),
                description=str(ex)
            )

        return DoServiceAction(ok=True, service_status=service_status)


class SettingsMutations(graphene.ObjectType):
    changeSettings = ChangeSettingsMutation.Field()
    changeSmtpSettings = ChangeSmtpSettingsMutation.Field()

    doServiceAction = DoServiceAction.Field()


settings_schema = graphene.Schema(
    query=SettingsQuery, mutation=SettingsMutations, auto_camelcase=False
)
