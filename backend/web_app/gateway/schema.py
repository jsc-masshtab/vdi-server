# -*- coding: utf-8 -*-
import graphene

from common.graphene_utils import ShortString
from common.models.pool import Pool
from common.models.settings import Settings
from common.models.vm_connection_data import VmConnectionData
from common.veil.veil_decorators import administrator_required

from web_app.gateway.gateway_connection import GatewayConnection


gateway_connection = GatewayConnection()

ConnectionTypesGraphene = graphene.Enum.from_enum(Pool.PoolConnectionTypes)


class GatewayType(graphene.ObjectType):
    vm_id = graphene.UUID()
    connection_type = ConnectionTypesGraphene()
    address = graphene.Field(ShortString)
    port = graphene.Int()


class GatewayQuery(graphene.ObjectType):
    vm_connection_data = graphene.List(GatewayType)

    @administrator_required
    async def resolve_vm_connection_data(self, _info, **kwargs):
        connection_data = (
            await VmConnectionData.query.where(VmConnectionData.active == True) # noqa
            .gino.all()
        )
        connection_data_list = []
        for conn in connection_data:
            data = GatewayType(
                vm_id=conn.vm_id,
                connection_type=conn.connection_type,
                address=conn.address,
                port=conn.port
            )
            connection_data_list.append(data)
        return connection_data_list


class StartConnections(graphene.Mutation):
    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, creator, **kwargs):
        await gateway_connection.start_connections()
        return StartConnections(ok=True)


class StartTkConnectionListener(graphene.Mutation):
    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, creator, **kwargs):
        await gateway_connection.start_tk_connection_listener()
        return StartTkConnectionListener(ok=True)


class SendSettingsToGateway(graphene.Mutation):
    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, creator, **kwargs):
        settings = await Settings.get_gateway_settings()
        await gateway_connection.change_settings_request(
            request_body=settings
        )
        return SendSettingsToGateway(ok=True)


class GatewayMutations(graphene.ObjectType):
    start_connections = StartConnections.Field()
    start_tk_connection_listener = StartTkConnectionListener.Field()
    send_settings_to_gateway = SendSettingsToGateway.Field()


gateway_schema = graphene.Schema(
    query=GatewayQuery, mutation=GatewayMutations, auto_camelcase=False
)
