# -*- coding: utf-8 -*-
from collections import OrderedDict
from enum import Enum

import graphene

from common.languages import _local_
from common.log.journal import system_logger
from common.models.settings import Settings
from common.utils import create_subprocess
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SilentError, SimpleError


class ServiceAction(Enum):
    """Действия над сервисами."""

    START = "start"
    STOP = "stop"
    RESTART = "restart"


ServiceActionGraphene = graphene.Enum.from_enum(ServiceAction)


class SettingsType(graphene.ObjectType):
    LANGUAGE = graphene.String()
    DEBUG = graphene.Boolean()
    VEIL_CACHE_TTL = graphene.Int()
    VEIL_CACHE_SERVER = graphene.String()
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
    hostname = graphene.String()
    port = graphene.Int()
    TLS = graphene.Boolean()
    SSL = graphene.Boolean()
    password = graphene.String()
    user = graphene.String()
    from_address = graphene.String()
    level = graphene.Int()


class ServiceGrapheneType(graphene.ObjectType):
    service_name = graphene.String()
    verbose_name = graphene.String()
    status = graphene.String()


class SettingsQuery(graphene.ObjectType):
    settings = graphene.Field(SettingsType)
    smtp_settings = graphene.Field(SmtpSettingsType)

    services = graphene.List(ServiceGrapheneType)

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
                _local_("Unable to get services info. {}.").format(stderr.decode()),
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
            except Exception as ex:
                raise SimpleError(
                    _local_("Output parsing error. {}.").format(str(ex)),
                    user=creator
                )

        # Form response
        service_graphene_type_list = []
        app_services = SettingsQuery._get_app_services_dict()

        for service_name, verbose_name in app_services.items():
            service_status = current_services.get(service_name, "stopped")
            service_graphene_type = ServiceGrapheneType(
                service_name=service_name,
                verbose_name=verbose_name,
                status=service_status)
            service_graphene_type_list.append(service_graphene_type)

        return service_graphene_type_list

    @staticmethod
    def _get_app_services_dict():
        """Get dictionary of services.

        {Service name: human friendly service name}.
        """
        app_services = OrderedDict([
            # external services
            ("apache2.service", _local_("Apache server")),
            ("postgresql.service", _local_("Database")),
            ("redis-server.service", "Redis"),
            # app services
            ("vdi-monitor_worker.service", _local_("Monitor worker")),
            ("vdi-pool_worker.service", _local_("Task worker")),
            ("vdi-web.service", _local_("Web application")),
        ])

        return app_services


class ChangeSettingsMutation(graphene.Mutation):
    class Arguments:
        LANGUAGE = graphene.String(description="Язык сообщений журнала")
        DEBUG = graphene.Boolean()
        VEIL_CACHE_TTL = graphene.Int()
        VEIL_CACHE_SERVER = graphene.String()
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
    async def mutate(self, _info, **kwargs):
        ok = await Settings.change_settings(**kwargs)
        return ChangeSettingsMutation(ok=ok)


class ChangeSmtpSettingsMutation(graphene.Mutation):
    class Arguments:
        hostname = graphene.String()
        port = graphene.Int()
        TLS = graphene.Boolean()
        SSL = graphene.Boolean()
        password = graphene.String()
        user = graphene.String()
        from_address = graphene.String()
        level = graphene.Int()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, **kwargs):
        ok = await Settings.change_smtp_settings(**kwargs)
        return ChangeSmtpSettingsMutation(ok=ok)


class DoServiceAction(graphene.Mutation):
    class Arguments:
        sudo_password = graphene.String()
        service_name = graphene.String()
        service_action = ServiceActionGraphene()
        check_errors = graphene.Boolean()

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, sudo_password, service_name, service_action,
                     check_errors=True, creator="system"):
        cmd = "echo {} | sudo -S timeout 50s systemctl {} {}".format(
            sudo_password, service_action, service_name)

        return_code, stdout, stderr = await create_subprocess(cmd)

        if check_errors and stderr:
            raise SimpleError(
                _local_("Error occurred during service action executing. {}.").format(stderr.decode()),
                description="Return code: {}".format(return_code),
                user=creator
            )

        await system_logger.info(_local_("Executed action {} for service {}").
                                 format(service_action, service_name), user=creator)

        return DoServiceAction(ok=True)


class SettingsMutations(graphene.ObjectType):
    changeSettings = ChangeSettingsMutation.Field()
    changeSmtpSettings = ChangeSmtpSettingsMutation.Field()

    doServiceAction = DoServiceAction.Field()


settings_schema = graphene.Schema(
    query=SettingsQuery, mutation=SettingsMutations, auto_camelcase=False
)
