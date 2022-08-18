# -*- coding: utf-8 -*-
import graphene

from common.graphene_utils import ShortString
from common.settings import MINIMUM_SUPPORTED_DESKTOP_THIN_CLIENT_VERSION


class BrokerInfoQuery(graphene.ObjectType):
    minimum_supported_desktop_thin_client_version = ShortString()

    async def resolve_minimum_supported_desktop_thin_client_version(self, info):
        return MINIMUM_SUPPORTED_DESKTOP_THIN_CLIENT_VERSION


broker_info_schema = graphene.Schema(
    query=BrokerInfoQuery, auto_camelcase=False
)
