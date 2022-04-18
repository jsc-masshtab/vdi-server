import graphene

from common.graphene_utils import ShortString
from common.veil.veil_gino import StatusGraphene
from common.veil.veil_graphene import (
    VeilResourceType,
    VeilShortEntityType
)


# Node aka Server
class NodeType(VeilResourceType):
    """Описание ноды на ECP VeiL."""

    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    status = StatusGraphene()
    domains_count = graphene.Int()
    management_ip = graphene.Field(ShortString)
    domains_on_count = graphene.Int()
    datacenter_name = graphene.Field(ShortString)
    cluster = graphene.Field(VeilShortEntityType)
    memory_count = graphene.Int()
    datacenter_id = graphene.UUID()
    built_in = graphene.Boolean()
    cpu_count = graphene.Int()
    hints = graphene.Int()
    tags = graphene.List(ShortString)
    controller = graphene.Field(VeilShortEntityType)
    version = graphene.Field(ShortString)
    ksm_pages_to_scan = graphene.Int()
    ballooning = graphene.Boolean()
    cluster_name = graphene.Field(ShortString)
    description = graphene.Field(ShortString)
    node_plus_controller_installation = graphene.Boolean()
    heartbeat_type = graphene.Field(ShortString)
    ipmi_username = graphene.Field(ShortString)
    ksm_merge_across_nodes = graphene.Int()
    fencing_type = graphene.Field(ShortString)
    ksm_enable = graphene.Int()
    ksm_sleep_time = graphene.Int()
