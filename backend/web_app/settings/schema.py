# -*- coding: utf-8 -*-
import graphene

from common.models.settings import Settings
from common.veil.veil_decorators import administrator_required


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


class SettingsQuery(graphene.ObjectType):
    settings = graphene.Field(SettingsType)
    smtp_settings = graphene.Field(SmtpSettingsType)

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


class SettingsMutations(graphene.ObjectType):
    changeSettings = ChangeSettingsMutation.Field()
    changeSmtpSettings = ChangeSmtpSettingsMutation.Field()


settings_schema = graphene.Schema(
    query=SettingsQuery, mutation=SettingsMutations, auto_camelcase=False
)
