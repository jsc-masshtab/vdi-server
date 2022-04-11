# -*- coding: utf-8 -*-
import graphene

from common.graphene_utils import ShortString
from common.veil.veil_gino import StatusGraphene
from common.veil.veil_graphene import (
    VeilResourceType,
    VeilShortEntityType
)


class ClusterType(VeilResourceType):
    """Описание сущности кластера."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    status = StatusGraphene()
    tags = graphene.List(ShortString)
    hints = graphene.Int()
    built_in = graphene.Boolean()
    cluster_fs_configured = graphene.Boolean()
    controller = graphene.Field(VeilShortEntityType)
    anti_affinity_enabled = graphene.Boolean()
    datacenter = graphene.Field(VeilShortEntityType)
    ha_autoselect = graphene.Boolean()
    quorum = graphene.Boolean()
    drs_strategy = graphene.Boolean()
    cpu_count = graphene.Int()
    cluster_fs_type = graphene.Field(ShortString)
    ha_timeout = graphene.Int()
    drs_check_timeout = graphene.Int()
    drs_deviation_limit = graphene.Float()
    nodes = graphene.List(VeilShortEntityType)
    nodes_count = graphene.Int()
    memory_count = graphene.Int()
    description = graphene.Field(ShortString)
    ha_retrycount = graphene.Int()
    drs_mode = graphene.Field(ShortString)
    drs_metrics_strategy = graphene.Field(ShortString)
