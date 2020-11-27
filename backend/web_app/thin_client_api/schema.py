# -*- coding: utf-8 -*-
# GraphQL schema

import graphene

from common.veil.veil_decorators import administrator_required
# from common.veil.veil_redis import REDIS_CLIENT
from common.languages import lang_init
from common.utils import extract_ordering_data
from sqlalchemy.sql import desc

from common.database import db
from common.models.active_tk_connection import ActiveTkConnection
from common.models.auth import User
from common.models.vm import Vm


_ = lang_init()


class ThinClientType(graphene.ObjectType):
    user_name = graphene.String()
    veil_connect_version = graphene.String()
    vm_name = graphene.String()
    tk_ip = graphene.String()
    tk_os = graphene.String()
    connected = graphene.DateTime()
    data_received = graphene.DateTime()  # время когда последний раз получили что-то по ws от тк

    @staticmethod
    async def create_from_db_data(tk_db_data):
        thin_client_type = ThinClientType()
        thin_client_type.user_name = tk_db_data.username
        thin_client_type.veil_connect_version = tk_db_data.veil_connect_version
        thin_client_type.vm_name = tk_db_data.verbose_name
        thin_client_type.tk_ip = tk_db_data.tk_ip
        thin_client_type.tk_os = tk_db_data.tk_os
        thin_client_type.connected = tk_db_data.connected
        thin_client_type.data_received = tk_db_data.data_received

        return thin_client_type


class ThinClientQuery(graphene.ObjectType):

    thin_clients_count = graphene.Int(default_value=0)

    thin_clients = graphene.List(ThinClientType, limit=graphene.Int(default_value=100),
                                 offset=graphene.Int(default_value=0),
                                 ordering=graphene.String(default_value='connected'))

    @administrator_required
    async def resolve_thin_clients_count(self, _info, **kwargs):
        users_count = await db.select([db.func.count()]).select_from(ActiveTkConnection).gino.scalar()
        return users_count

    @administrator_required
    async def resolve_thin_clients(self, _info, limit, offset, ordering, **kwargs):
        query = db.select([
            ActiveTkConnection.veil_connect_version,
            ActiveTkConnection.tk_ip,
            ActiveTkConnection.tk_os,
            ActiveTkConnection.connected,
            ActiveTkConnection.data_received,
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


thin_client_schema = graphene.Schema(query=ThinClientQuery, auto_camelcase=False)
