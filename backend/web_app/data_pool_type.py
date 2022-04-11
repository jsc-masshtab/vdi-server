# -*- coding: utf-8 -*-
import graphene

from common.graphene_utils import ShortString
from common.veil.veil_gino import StatusGraphene
from common.veil.veil_graphene import (
    VeilResourceType,
    VeilShortEntityType
)


class DataPoolType(VeilResourceType):
    """Описание пула-данных на ECP VeiL."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    description = graphene.Field(ShortString)
    status = StatusGraphene()
    controller = graphene.Field(VeilShortEntityType)
    tags = graphene.List(ShortString)
    hints = graphene.Int()
    built_in = graphene.Boolean()
    free_space = graphene.Int()
    used_space = graphene.Int()
    vdisk_count = graphene.Int()
    type = graphene.Field(ShortString)
    file_count = graphene.Int()
    size = graphene.Int()
    iso_count = graphene.Int()
    nodes_connected = graphene.List(VeilShortEntityType)
    zfs_pool = graphene.UUID()
    shared_storage = graphene.Field(VeilShortEntityType)
    cluster_storage = graphene.Field(VeilShortEntityType)
    lun = graphene.JSONString()
    options = graphene.JSONString()
