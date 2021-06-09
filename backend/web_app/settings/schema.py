# -*- coding: utf-8 -*-
import graphene

from common.languages import lang_init
from common.models.settings import Settings
from common.veil.veil_decorators import administrator_required


_ = lang_init()


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


class SettingsQuery(graphene.ObjectType):
    settings = graphene.Field(SettingsType)

    @administrator_required
    async def resolve_settings(self, _info, **kwargs):
        settings = await Settings.get_settings()
        settings_list = SettingsType(**settings)
        return settings_list


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


class SettingsMutations(graphene.ObjectType):
    changeSettings = ChangeSettingsMutation.Field()


settings_schema = graphene.Schema(
    query=SettingsQuery, mutation=SettingsMutations, auto_camelcase=False
)
