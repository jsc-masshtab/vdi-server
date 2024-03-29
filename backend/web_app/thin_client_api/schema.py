# -*- coding: utf-8 -*-
import json
import textwrap

import graphene

from sqlalchemy import and_
from sqlalchemy.sql import desc

from common.database import db
from common.graphene_utils import ShortString
from common.languages import _local_
from common.log.journal import system_logger
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from common.models.pool import Pool
from common.models.tk_vm_connection import TkVmConnection
from common.models.vm import Vm
from common.settings import REDIS_TEXT_MSG_CHANNEL, REDIS_THIN_CLIENT_CMD_CHANNEL
from common.subscription_sources import WsMessageDirection, WsMessageType
from common.utils import extract_ordering_data
from common.veil.veil_decorators import administrator_required
from common.veil.veil_errors import SilentError, ValidationError
from common.veil.veil_redis import ThinClientCmd, publish_to_redis

ConnectionTypesGraphene = graphene.Enum.from_enum(Pool.PoolConnectionTypes)


class ThinClientType(graphene.ObjectType):
    conn_id = graphene.UUID()
    user_id = graphene.UUID()
    user_name = graphene.Field(ShortString)
    veil_connect_version = graphene.Field(ShortString)
    vm_name = graphene.Field(ShortString)
    tk_ip = graphene.Field(ShortString)
    tk_os = graphene.Field(ShortString)
    connected = graphene.DateTime()
    disconnected = graphene.DateTime()
    data_received = (
        graphene.DateTime()
    )  # время когда последний раз получили что-то по ws от тк
    last_interaction = graphene.DateTime()  # время последнего взаимоействия юзера с гуи
    is_afk = graphene.Boolean()  # AFK ли пользователь

    connection_type = ConnectionTypesGraphene()
    is_connection_secure = graphene.Boolean()

    read_speed = graphene.Int()
    write_speed = graphene.Int()
    avg_rtt = graphene.Float()
    loss_percentage = graphene.Int()

    mac_address = graphene.Field(ShortString)
    hostname = graphene.Field(ShortString)

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

        thin_client_type.read_speed = tk_db_data.read_speed
        thin_client_type.write_speed = tk_db_data.write_speed
        thin_client_type.avg_rtt = tk_db_data.avg_rtt
        thin_client_type.loss_percentage = tk_db_data.loss_percentage

        thin_client_type.mac_address = tk_db_data.mac_address
        thin_client_type.hostname = tk_db_data.hostname

        # AFK
        if tk_db_data.disconnected:
            thin_client_type.is_afk = None
        else:
            thin_client_type.is_afk = await ActiveTkConnection.afk(tk_db_data.last_interaction)

        return thin_client_type


class ThinClientQuery(graphene.ObjectType):

    thin_clients_count = graphene.Int(get_disconnected=graphene.Boolean(),
                                      user_id=graphene.UUID(),
                                      default_value=0)

    thin_clients = graphene.List(
        ThinClientType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        ordering=ShortString(default_value="-connected"),
        get_disconnected=graphene.Boolean(default_value=False),
        user_id=graphene.UUID(default_value=None),
    )

    thin_client = graphene.Field(ThinClientType, conn_id=graphene.UUID())

    @administrator_required
    async def resolve_thin_clients_count(self, _info, **kwargs):

        conn_count = await ActiveTkConnection.get_thin_clients_conn_count(
            kwargs.get("get_disconnected"), kwargs.get("user_id"))
        return conn_count

    @administrator_required
    async def resolve_thin_clients(
        self, _info, limit, offset, ordering, get_disconnected, user_id=None, **kwargs
    ):
        query = ThinClientQuery.build_thin_client_query()

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

        # conversion
        graphene_types = [
            ThinClientType.create_from_db_data(tk_db_data)
            for tk_db_data in tk_db_data_container
        ]
        return graphene_types

    @administrator_required
    async def resolve_thin_client(self, _info, conn_id, **kwargs):
        query = ThinClientQuery.build_thin_client_query()

        tk_conn = await query.where(ActiveTkConnection.id == conn_id).gino.first()
        if not tk_conn:
            raise SilentError(_local_("No connection information with id {}.").format(conn_id))

        return ThinClientType.create_from_db_data(tk_conn)

    @staticmethod
    def build_thin_client_query():
        # Найти подключения к ВМ с последней датой подключения (максимальной)
        subquery_vm_conn = db.select(
            [
                TkVmConnection.tk_connection_id,
                db.func.max(TkVmConnection.connected_to_vm).label("max_connected_to_vm")
            ]).\
            where((TkVmConnection.disconnected_from_vm == None)).group_by(TkVmConnection.tk_connection_id)  # noqa

        subquery_vm_conn = subquery_vm_conn.alias("subquery_vm_conn")

        # Джойн на себя (TkVmConnection) чтобы получить остальные данные TkVmConnection
        subquery_vm_conn_2 = db.select(
            [
                TkVmConnection.vm_id,
                TkVmConnection.tk_connection_id,
                TkVmConnection.connection_type,
                TkVmConnection.is_connection_secure,
                TkVmConnection.read_speed,
                TkVmConnection.write_speed,
                TkVmConnection.avg_rtt,
                TkVmConnection.loss_percentage
            ]).\
            select_from(
            subquery_vm_conn.join(TkVmConnection,
                                  (subquery_vm_conn.c.tk_connection_id == TkVmConnection.tk_connection_id) &  # noqa
                                  (subquery_vm_conn.c.max_connected_to_vm == TkVmConnection.connected_to_vm)))

        subquery_vm_conn_2 = subquery_vm_conn_2.alias("subquery_vm_conn_2")

        # Финальный запрос. Получение соединений ТК с VDI с данными о последнем активном подключении к ВМ(если имеется)
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
                ActiveTkConnection.mac_address,
                ActiveTkConnection.hostname,
                User.id.label("user_id"),
                User.username,
                Vm.verbose_name,
                subquery_vm_conn_2.c.connection_type,
                subquery_vm_conn_2.c.is_connection_secure,
                subquery_vm_conn_2.c.read_speed,
                subquery_vm_conn_2.c.write_speed,
                subquery_vm_conn_2.c.avg_rtt,
                subquery_vm_conn_2.c.loss_percentage
            ]
        )

        query = query.select_from(
            ActiveTkConnection.join(
                User, ActiveTkConnection.user_id == User.id, isouter=True).join(
                subquery_vm_conn_2, ActiveTkConnection.id == subquery_vm_conn_2.c.tk_connection_id, isouter=True).join(
                Vm, subquery_vm_conn_2.c.vm_id == Vm.id, isouter=True)
        )

        return query


class DisconnectThinClientMutation(graphene.Mutation):
    """Команда клиентам отключиться.

    Просим клиента отключиться по ws и по удаленному протоколу, если клиент подключен к ВМ в данный момент.
    Если указан conn_id, то завершаем конкретое соединение
    Если указан user_id, то завершаем соединения соответствующего пользоватедя
    Если ничего не указано, то массового завершаем все соединения
    """

    class Arguments:
        conn_id = graphene.UUID(required=False)
        user_id = graphene.UUID(required=False)

    ok = graphene.Boolean()

    @administrator_required
    async def mutate(self, _info, creator, **kwargs):
        cmd_dict = dict(command=ThinClientCmd.DISCONNECT.name)

        add_message = ""
        conn_id = kwargs.get("conn_id")
        user_id = kwargs.get("user_id")

        if conn_id is None and user_id is None:
            add_message = _local_("All connections.")
        elif conn_id:
            cmd_dict.update(conn_id=str(conn_id))
            add_message = _local_("Connection id: {}.").format(conn_id)

        elif user_id:
            cmd_dict.update(user_id=str(user_id))
            user = await User.get(user_id)
            if not user:
                raise ValidationError(_local_("No such user."))
            add_message = _local_("Connections of user: {}.").format(user.username)

        await publish_to_redis(REDIS_THIN_CLIENT_CMD_CHANNEL, json.dumps(cmd_dict))

        base_message = _local_("Thin client disconnect requested.")
        await system_logger.info(base_message + " " + add_message, user=creator)

        return DisconnectThinClientMutation(ok=True)


class SendMessageToThinClientMutation(graphene.Mutation):
    """Посылка текстового сообщения пользователям ТК.

    Если recipient_id==None, то сообщение шлется всем текущим пользователям ТК
    """

    class Arguments:
        recipient_id = graphene.UUID(default_value=None, description="id получателя")
        message = ShortString(required=True, description="Текстовое сообщение")

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
                raise SilentError(
                    _local_("User {} does not exist.").format(recipient_id))
            message_data_dict.update(recipient_id=str(recipient_id))

        await publish_to_redis(REDIS_TEXT_MSG_CHANNEL, json.dumps(message_data_dict))

        return SendMessageToThinClientMutation(ok=True)


class ThinClientMutations(graphene.ObjectType):
    disconnectThinClient = DisconnectThinClientMutation.Field()
    sendMessageToThinClient = SendMessageToThinClientMutation.Field()


thin_client_schema = graphene.Schema(
    query=ThinClientQuery, mutation=ThinClientMutations, auto_camelcase=False
)
