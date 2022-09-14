# -*- coding: utf-8 -*-
import graphene

from sqlalchemy import text

from common.database import db
from common.graphene_utils import ShortString
from common.languages import _local_
from common.models.auth import User as UserModel
from common.models.vm import Vm
from common.models.vm_connection_data import VmConnectionData
from common.utils import convert_gino_model_to_graphene_type
from common.veil.veil_errors import SimpleError
from common.veil.veil_gino import (
    StatusGraphene
)
from common.veil.veil_graphene import (
    VeilResourceType,
    VeilShortEntityType,
    VeilTagsType,
    VmState,
)

from web_app.auth.user_schema import UserType
from web_app.data_pool_type import DataPoolType
from web_app.journal.schema import EntityType as TypeEntity, EventType


class VmConnectionType(VeilResourceType):
    """Данные для подключения по спайс и VNC из вебки."""

    password = graphene.Field(ShortString)
    host = graphene.Field(ShortString)
    token = graphene.Field(ShortString)
    connection_url = graphene.Field(ShortString)
    connection_type = graphene.Field(ShortString)


class VmConnectionDataTkType(VeilResourceType):
    """Данные подключения к ВМ для тонкого клиента."""

    id = graphene.UUID()
    vm_id = graphene.UUID()
    connection_type = graphene.Field(ShortString)
    address = graphene.Field(ShortString)
    port = graphene.Int()
    active = graphene.Boolean()


class VmBackupType(VeilResourceType):
    file_id = graphene.Field(ShortString)
    filename = graphene.Field(ShortString)
    size = graphene.Field(ShortString)
    assignment_type = graphene.Field(ShortString)
    datapool = graphene.Field(DataPoolType)
    node = graphene.Field(VeilShortEntityType)
    vm_id = graphene.Field(ShortString)
    status = StatusGraphene()


class VmType(VeilResourceType):
    id = graphene.UUID()
    verbose_name = graphene.Field(ShortString)
    status = StatusGraphene()
    controller = graphene.Field(VeilShortEntityType)
    resource_pool = graphene.Field(VeilShortEntityType)
    memory_count = graphene.Int()
    cpu_count = graphene.Int()
    template = graphene.Boolean()
    tags = graphene.List(ShortString)
    hints = graphene.Int()
    user_power_state = VmState(description="Питание")
    safety = graphene.Boolean()
    boot_type = graphene.Field(ShortString)
    start_on_boot = graphene.Boolean()
    cloud_init = graphene.Boolean()
    disastery_enabled = graphene.Boolean()
    thin = graphene.Boolean()
    ha_retrycount = graphene.Boolean()
    ha_timeout = graphene.Int()
    ha_enabled = graphene.Boolean()
    clean_type = graphene.Field(ShortString)
    machine = graphene.Field(ShortString)
    graphics_password = graphene.Field(ShortString)
    remote_access = graphene.Boolean()
    bootmenu_timeout = graphene.Int()
    os_type = graphene.Field(ShortString)
    cpu_type = graphene.Field(ShortString)
    description = graphene.Field(ShortString)
    guest_agent = graphene.Boolean()
    os_version = graphene.Field(ShortString)
    spice_stream = graphene.Boolean()
    tablet = graphene.Boolean()
    parent = graphene.Field(VeilShortEntityType)
    parent_name = graphene.Field(ShortString)
    hostname = graphene.Field(ShortString)
    address = graphene.List(ShortString)
    domain_tags = graphene.List(VeilTagsType)
    pool_name = graphene.Field(ShortString)  # название пула, в котором ВМ из локальной БД
    user = graphene.Field(UserType)
    assigned_users = graphene.List(
        UserType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        username=ShortString()
    )
    assigned_users_count = graphene.Int()
    possible_users = graphene.List(
        UserType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
        username=ShortString()
    )
    possible_users_count = graphene.Int()

    # qemu_state = graphene.Boolean(description='Состояние гостевого агента')
    qemu_state = VmState(description="Состояние гостевого агента")
    node = graphene.Field(VeilShortEntityType)
    backups = graphene.List(VmBackupType)

    # Список событий для отдельной ВМ и отдельное событие внутри пула
    count = graphene.Int()
    events = graphene.List(
        EventType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )
    event = graphene.Field(EventType, event_id=graphene.UUID())
    spice_connection = graphene.Field(VmConnectionType)
    vnc_connection = graphene.Field(VmConnectionType)

    vm_connection_data_list = graphene.List(
        VmConnectionDataTkType,
        limit=graphene.Int(default_value=100),
        offset=graphene.Int(default_value=0),
    )
    vm_connection_data_count = graphene.Int()

    async def resolve_user(self, _info):
        vm = await Vm.get(self.id)
        username = await vm.username if vm else None
        return UserType(username=username)

    async def resolve_assigned_users(self, _info, limit, offset, username=None):
        """Получить список пользователей ВМ."""
        vm = await Vm.get(self.id)
        if vm:
            users_query = await vm.get_users_query()

            if username:
                users_query = users_query.where(UserModel.username.ilike(f"%{username}%"))

            users = await users_query.limit(limit).offset(offset).gino.all()
            objects = [UserType.instance_to_type(user) for user in users]
            objects.sort(key=lambda name: name.username)
            return objects
        return list()

    async def resolve_assigned_users_count(self, _info):
        vm = await Vm.get(self.id)
        count = await vm.get_users_count()
        return count

    async def get_possible_users_query(self):
        vm = await Vm.get(self.id)
        vm_assigned_users_query = await vm.get_users_query()

        pool = await vm.pool
        pool_assigned_users_query = await pool.get_assigned_users_query()

        vm_possible_users_query = pool_assigned_users_query.where(UserModel.id.notin_(
            db.select([text("query.id")]).select_from(vm_assigned_users_query.alias("query"))))

        return vm_possible_users_query

    async def resolve_possible_users(self, _info, limit, offset, username=None):
        """Получить список пользователей пула, возможных для назначения на текущую ВМ."""
        vm_possible_users_query = await self.get_possible_users_query()

        if username:
            vm_possible_users_query = vm_possible_users_query.where(UserModel.username.ilike(f"%{username}%"))

        vm_possible_users_query = vm_possible_users_query.order_by(UserModel.username)

        return await vm_possible_users_query.limit(limit).offset(offset).gino.all()

    async def resolve_possible_users_count(self, _info):
        vm_possible_users_query = await self.get_possible_users_query()
        count = await db.select([db.func.count()]).select_from(vm_possible_users_query.alias()).gino.scalar()
        return count

    async def resolve_count(self, _info, **kwargs):
        vm_obj = await Vm.get(self.id)
        events_count = await vm_obj.events_count()
        return events_count

    async def resolve_events(self, _info, limit, offset):
        vm_obj = await Vm.get(self.id)
        events = await vm_obj.events(limit=limit, offset=offset)
        event_type_list = [
            EventType(
                read_by=[UserType(**user.__values__) for user in event.read_by],
                entity=[TypeEntity(**entity.__values__) for entity in event.entity],
                **event.__values__
            )
            for event in events
        ]
        return event_type_list

    async def resolve_event(self, _info, event_id):
        event = await Vm.event(event_id)
        event_type = EventType(
            read_by=[UserType(**user.__values__) for user in event.read_by],
            entity=[entity for entity in event.entity],
            **event.__values__
        )
        return event_type

    async def resolve_backups(self, _info, **kwargs):
        vm_obj = await Vm.get(self.id)
        domain_entity = await vm_obj.vm_client
        if domain_entity:
            await domain_entity.info()
            # Список бэкапов ВМ
            response = await domain_entity.backup_list()
            veil_backups_list = list()
            backups_list = list()
            for data in response.response:
                backup = data.public_attrs
                backup["file_id"] = backup["api_object_id"]
                backup["node"] = self.node
                backup["vm_id"] = self.id
                backups_list.append(backup)

            for data in backups_list:
                veil_backups_list.append(VmBackupType(**data))

            return veil_backups_list

    async def resolve_spice_connection(self, _info, **kwargs):
        vm_obj = await Vm.get(self.id)
        domain_entity = await vm_obj.vm_client
        await domain_entity.info()
        if domain_entity.powered:
            spice = await domain_entity.spice_conn()
            if spice and spice.valid:
                return VmConnectionType(password=spice.password,
                                        host=spice.host,
                                        token=spice.token,
                                        connection_url=spice.connection_url,
                                        connection_type=spice.connection_type)
            raise SimpleError(_local_("Missing connection spice data."))

    async def resolve_vnc_connection(self, _info, **kwargs):
        vm_obj = await Vm.get(self.id)
        domain_entity = await vm_obj.vm_client
        await domain_entity.info()
        if domain_entity.powered:
            vnc = await domain_entity.vnc_conn()
            if vnc and vnc.valid:
                return VmConnectionType(password=vnc.password,
                                        host=vnc.host,
                                        token=vnc.token,
                                        connection_url=vnc.connection_url,
                                        connection_type=vnc.connection_type)
            raise SimpleError(_local_("Missing connection vnc data."))

    async def resolve_vm_connection_data_list(self, _info, limit, offset):
        vm = await Vm.get(self.id)

        query = VmConnectionData.get_vm_connection_data_list_query(vm.id)
        vm_connection_data_list = await query.limit(limit).offset(offset).gino.all()

        vm_connection_data_tk_type_list = [convert_gino_model_to_graphene_type(item, VmConnectionDataTkType)
                                           for item in vm_connection_data_list]
        return vm_connection_data_tk_type_list

    async def resolve_vm_connection_data_count(self, _info):
        vm = await Vm.get(self.id)
        query = VmConnectionData.get_vm_connection_data_list_query(vm.id)
        count = await db.select([db.func.count()]).select_from(query.alias()).gino.scalar()
        return count
