# -*- coding: utf-8 -*-
# GraphQL schema

import graphene
import json
from datetime import timedelta, datetime, timezone

from common.settings import REDIS_THIN_CLIENT_CMD_CHANNEL

from common.veil.veil_decorators import administrator_required
from common.veil.veil_redis import REDIS_CLIENT, ThinClientCmd

from common.languages import lang_init
from common.utils import extract_ordering_data
from sqlalchemy.sql import desc

from common.database import db
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from common.models.vm import Vm


_ = lang_init()


class ThinClientType(graphene.ObjectType):
    conn_id = graphene.UUID()
    user_name = graphene.String()
    veil_connect_version = graphene.String()
    vm_name = graphene.String()
    tk_ip = graphene.String()
    tk_os = graphene.String()
    connected = graphene.DateTime()
    data_received = graphene.DateTime()  # время когда последний раз получили что-то по ws от тк
    last_interaction = graphene.DateTime()  # время последнего взаимоействия юзера с гуи
    is_afk = graphene.Boolean()  # AFK ли пользователь

    async def resolve_is_afk(self, _info):
        afk_timeout = 300  # как в WoW
        time_delta = timedelta(seconds=afk_timeout)
        cur_time = datetime.now(timezone.utc)
        return bool((cur_time - self.last_interaction) > time_delta)

    @staticmethod
    async def create_from_db_data(tk_db_data):

        thin_client_type = ThinClientType()
        thin_client_type.conn_id = tk_db_data.id
        thin_client_type.user_name = tk_db_data.username
        thin_client_type.veil_connect_version = tk_db_data.veil_connect_version
        thin_client_type.vm_name = tk_db_data.verbose_name
        thin_client_type.tk_ip = tk_db_data.tk_ip
        thin_client_type.tk_os = tk_db_data.tk_os
        thin_client_type.connected = tk_db_data.connected
        thin_client_type.data_received = tk_db_data.data_received
        thin_client_type.last_interaction = tk_db_data.last_interaction

        return thin_client_type


class ThinClientQuery(graphene.ObjectType):

    thin_clients_count = graphene.Int(default_value=0)

    thin_clients = graphene.List(ThinClientType, limit=graphene.Int(default_value=100),
                                 offset=graphene.Int(default_value=0),
                                 ordering=graphene.String(default_value='connected'))

    @administrator_required
    async def resolve_thin_clients_count(self, _info, **kwargs):
        conn_count = await ActiveTkConnection.get_active_thin_clients_count()
        return conn_count

    @administrator_required
    async def resolve_thin_clients(self, _info, limit, offset, ordering, **kwargs):
        query = db.select([
            ActiveTkConnection.id,
            ActiveTkConnection.veil_connect_version,
            ActiveTkConnection.tk_ip,
            ActiveTkConnection.tk_os,
            ActiveTkConnection.connected,
            ActiveTkConnection.data_received,
            ActiveTkConnection.last_interaction,
            User.username,
            Vm.verbose_name
        ])

        query = query.select_from(ActiveTkConnection.join(User, ActiveTkConnection.user_id == User.id).
                                  join(Vm, ActiveTkConnection.vm_id == Vm.id, isouter=True))

        # ordering
        ordering_sp, reverse = extract_ordering_data(ordering)
        if ordering_sp == 'user_name':
            query = query.order_by(desc(User.username)) if reverse else query.order_by(User.username)
        elif ordering_sp == 'vm_name':
            query = query.order_by(desc(Vm.verbose_name)) if reverse else query.order_by(Vm.verbose_name)
        else:
            query = ActiveTkConnection.build_ordering(query, ordering)
        #
        # request to db
        tk_db_data_container = await query.limit(limit).offset(offset).gino.all()
        # conversion
        task_graphene_types = [
            ThinClientType.create_from_db_data(tk_db_data)
            for tk_db_data in tk_db_data_container
        ]
        return task_graphene_types


class DisconnectThinClientMutation(graphene.Mutation):
    """Команда клиенту отключиться. Просим клиента отключиться по ws и по удаленному протоколу,
    если клиент подключен к ВМ в данный момент"""
    class Arguments:
        conn_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, conn_id, **kwargs):
        cmd_dict = dict(command=ThinClientCmd.DISCONNECT.name, conn_id=str(conn_id))
        REDIS_CLIENT.publish(REDIS_THIN_CLIENT_CMD_CHANNEL, json.dumps(cmd_dict))

        return DisconnectThinClientMutation(ok=True)


class ThinClientMutations(graphene.ObjectType):
    disconnectThinClient = DisconnectThinClientMutation.Field()


thin_client_schema = graphene.Schema(query=ThinClientQuery, mutation=ThinClientMutations, auto_camelcase=False)
