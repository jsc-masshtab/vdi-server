# -*- coding: utf-8 -*-
import json
import textwrap
from datetime import datetime, timedelta, timezone

import graphene

from sqlalchemy import and_
from sqlalchemy.sql import desc

from common.database import db
from common.languages import lang_init
from common.models.active_tk_connection import (
    ActiveTkConnection,
    TkConnectionStatistics,
)
from common.models.auth import User
from common.models.pool import Pool
from common.models.vm import Vm
from common.settings import REDIS_TEXT_MSG_CHANNEL, REDIS_THIN_CLIENT_CMD_CHANNEL
from common.subscription_sources import WsMessageDirection, WsMessageType
from common.utils import extract_ordering_data
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SilentError
from common.veil.veil_redis import REDIS_CLIENT, ThinClientCmd

_ = lang_init()

ConnectionTypesGraphene = graphene.Enum.from_enum(Pool.PoolConnectionTypes)


class ThinClientType(graphene.ObjectType):
    conn_id = graphene.UUID()
    user_id = graphene.UUID()
    user_name = graphene.String()
    veil_connect_version = graphene.String()
    vm_name = graphene.String()
    tk_ip = graphene.String()
    tk_os = graphene.String()
    connected = graphene.DateTime()
    disconnected = graphene.DateTime()
    data_received = (
        graphene.DateTime()
    )  # время когда последний раз получили что-то по ws от тк
    last_interaction = graphene.DateTime()  # время последнего взаимоействия юзера с гуи
    is_afk = graphene.Boolean()  # AFK ли пользователь

    connection_type = ConnectionTypesGraphene()
    is_connection_secure = graphene.Boolean()

    async def resolve_is_afk(self, _info):

        if (
            self.last_interaction is None
        ):  # Если от клиента не было активности вообще, то считаем afk
            return True
        else:
            afk_timeout = 300  # как в WoW
            time_delta = timedelta(seconds=afk_timeout)
            cur_time = datetime.now(timezone.utc)
            return bool((cur_time - self.last_interaction) > time_delta)

    @staticmethod
    async def create_from_db_data(tk_db_data):
        thin_client_type = ThinClientType()
        thin_client_type.conn_id = tk_db_data.conn_id
        thin_client_type.user_id = tk_db_data.user_id
        thin_client_type.user_name = tk_db_data.username
        thin_client_type.veil_connect_version = tk_db_data.veil_connect_version
        thin_client_type.vm_name = tk_db_data.verbose_name
        thin_client_type.tk_ip = tk_db_data.tk_ip
        thin_client_type.tk_os = tk_db_data.tk_os
        thin_client_type.connected = tk_db_data.connected
        thin_client_type.disconnected = tk_db_data.disconnected
        thin_client_type.data_received = tk_db_data.data_received
        thin_client_type.last_interaction = tk_db_data.last_interaction
        thin_client_type.connection_type = tk_db_data.connection_type
        thin_client_type.is_connection_secure = tk_db_data.is_connection_secure

        return thin_client_type


class ThinClientConnStatType(graphene.ObjectType):
    id = graphene.UUID()
    conn_id = graphene.UUID()
    message = graphene.String()
    created = graphene.DateTime()

    @staticmethod
    async def create_from_db_data(tk_db_data):

        tk_conn_stat_type = ThinClientConnStatType()
        tk_conn_stat_type.id = tk_db_data.id
        tk_conn_stat_type.conn_id = tk_db_data.conn_id
        tk_conn_stat_type.message = tk_db_data.message
        tk_conn_stat_type.created = tk_db_data.created

        return tk_conn_stat_type


class ThinClientQuery(graphene.ObjectType):

    thin_clients_count = graphene.Int(get_disconnected=graphene.Boolean(),
                                      user_id=graphene.UUID(),
                                      default_value=0)

    thin_clients = graphene.List(
        ThinClientType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        ordering=graphene.String(default_value="connected"),
        get_disconnected=graphene.Boolean(default_value=False),
        user_id=graphene.UUID(default_value=None),
    )

    thin_clients_statistics = graphene.List(
        ThinClientConnStatType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        ordering=graphene.String(default_value="created"),
        conn_id=graphene.UUID(default_value=None),
        user_id=graphene.UUID(default_value=None),
    )

    @administrator_required
    async def resolve_thin_clients_count(self, _info, **kwargs):

        conn_count = await ActiveTkConnection.get_thin_clients_conn_count(
            kwargs.get("get_disconnected"), kwargs.get("user_id"))
        return conn_count

    @administrator_required
    async def resolve_thin_clients(
        self, _info, limit, offset, ordering, get_disconnected, user_id=None, **kwargs
    ):
        query = db.select(
            [
                ActiveTkConnection.id.label("conn_id"),
                ActiveTkConnection.veil_connect_version,
                ActiveTkConnection.tk_ip,
                ActiveTkConnection.tk_os,
                ActiveTkConnection.connected,
                ActiveTkConnection.disconnected,
                ActiveTkConnection.data_received,
                ActiveTkConnection.last_interaction,
                ActiveTkConnection.connection_type,
                ActiveTkConnection.is_connection_secure,
                User.id.label("user_id"),
                User.username,
                Vm.verbose_name,
            ]
        )

        query = query.select_from(
            ActiveTkConnection.join(User, ActiveTkConnection.user_id == User.id).join(
                Vm, ActiveTkConnection.vm_id == Vm.id, isouter=True
            )
        )

        # ordering
        ordering_sp, reverse = extract_ordering_data(ordering)
        if ordering_sp == "user_name":
            query = (
                query.order_by(desc(User.username))
                if reverse
                else query.order_by(User.username)
            )
        elif ordering_sp == "vm_name":
            query = (
                query.order_by(desc(Vm.verbose_name))
                if reverse
                else query.order_by(Vm.verbose_name)
            )
        else:
            query = ActiveTkConnection.build_ordering(query, ordering)

        # filter.
        filters = ActiveTkConnection.build_thin_clients_filters(get_disconnected, user_id)
        if filters:
            query = query.where(and_(*filters))

        # request to db
        tk_db_data_container = await query.limit(limit).offset(offset).gino.all()
        # print('tk_db_data_container ', tk_db_data_container, flush=True)
        # conversion
        graphene_types = [
            ThinClientType.create_from_db_data(tk_db_data)
            for tk_db_data in tk_db_data_container
        ]
        return graphene_types

    @administrator_required
    async def resolve_thin_clients_statistics(
        self, _info, limit, offset, ordering, conn_id=None, user_id=None, **kwargs
    ):

        query = db.select(
            [
                TkConnectionStatistics.id,
                TkConnectionStatistics.conn_id,
                TkConnectionStatistics.message,
                TkConnectionStatistics.created,
            ]
        )

        query = query.select_from(
            TkConnectionStatistics.join(ActiveTkConnection, isouter=True)
        )

        # ordering
        query = TkConnectionStatistics.build_ordering(query, ordering)

        # filtering
        filters = ThinClientQuery.build_thin_clients_stats_filters(conn_id, user_id)
        if filters:
            query = query.where(and_(*filters))

        tk_stat_db_data_container = await query.limit(limit).offset(offset).gino.all()

        # conversion
        graphene_types = [
            ThinClientConnStatType.create_from_db_data(tk_db_data)
            for tk_db_data in tk_stat_db_data_container
        ]
        return graphene_types

    @staticmethod
    def build_thin_clients_stats_filters(conn_id, user_id):
        """Получть статистику либо по определенному соединению, либо по соеднинениям определенного пользователя."""
        filters = []
        if conn_id:
            filters.append(ActiveTkConnection.id == conn_id)
        if user_id:
            filters.append(ActiveTkConnection.user_id == user_id)

        return filters


class DisconnectThinClientMutation(graphene.Mutation):
    """Команда клиенту отключиться.

    Просим клиента отключиться по ws и по удаленному протоколу, если клиент подключен к ВМ в данный момент.
    """

    class Arguments:
        conn_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, conn_id, **kwargs):
        cmd_dict = dict(command=ThinClientCmd.DISCONNECT.name, conn_id=str(conn_id))
        REDIS_CLIENT.publish(REDIS_THIN_CLIENT_CMD_CHANNEL, json.dumps(cmd_dict))

        return DisconnectThinClientMutation(ok=True)


class SendMessageToThinClientMutation(graphene.Mutation):
    """Посылка текстового сообщения пользователям ТК.

    Если recipient_id==None, то сообщение шлется всем текущим пользователям ТК
    """

    class Arguments:
        recipient_id = graphene.UUID(default_value=None, description="id получателя")
        message = graphene.String(required=True, description="Текстовое сообщение")

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, message, creator, **kwargs):

        shorten_msg = textwrap.shorten(message, width=2048)

        message_data_dict = dict(
            msg_type=WsMessageType.TEXT_MSG.value,
            sender_name=creator,  # шлем имя так как юзер ТК не может иметь список админов,
            # поэтому id был бы ему бесполезен
            message=shorten_msg,
            direction=WsMessageDirection.ADMIN_TO_USER.value,
        )

        # Добавляем данные о получателе если есть
        recipient_id = kwargs.get("recipient_id")
        if recipient_id:
            user = await User.get(recipient_id)
            if not user:
                raise SilentError(_("User {} does not exist.").format(recipient_id))
            message_data_dict.update(recipient_id=str(recipient_id))

        REDIS_CLIENT.publish(REDIS_TEXT_MSG_CHANNEL, json.dumps(message_data_dict))

        return SendMessageToThinClientMutation(ok=True)


class ThinClientMutations(graphene.ObjectType):
    disconnectThinClient = DisconnectThinClientMutation.Field()
    sendMessageToThinClient = SendMessageToThinClientMutation.Field()


thin_client_schema = graphene.Schema(
    query=ThinClientQuery, mutation=ThinClientMutations, auto_camelcase=False
)
