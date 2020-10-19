# -*- coding: utf-8 -*-
# GraphQL schema

import graphene

from common.veil.veil_decorators import administrator_required
from common.veil.veil_redis import get_thin_clients_count
from common.languages import lang_init


_ = lang_init()


class ThinClientQuery(graphene.ObjectType):

    thin_clients_count = graphene.Int(default_value=0)

    @administrator_required
    async def resolve_thin_clients_count(self, _info, **kwargs):
        return get_thin_clients_count()


thin_client_schema = graphene.Schema(query=ThinClientQuery, auto_camelcase=False)
