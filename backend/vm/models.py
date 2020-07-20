# -*- coding: utf-8 -*-
import uuid
import re
import asyncio

from sqlalchemy.dialects.postgresql import UUID
import tornado.gen
from asyncpg.exceptions import UniqueViolationError

from database import db, get_list_of_values_from_db, EntityType
from common.veil_errors import BadRequest, HttpError, VmCreationError, SimpleError, ServerError
from vm.veil_client import VmHttpClient
from auth.models import Entity, EntityRoleOwner, User

from languages import lang_init
from journal.journal import Log as log


_ = lang_init()


class Vm(db.Model):
    """
    ACTIONS = ('start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot')
    POWER_STATES = ('unknown', 'power off', 'power on and suspended', 'power on')
    """
    # TODO: положить в таблицу данные о удаленном подключении из ECP
    # TODO: ip address of domain?
    # TODO: port of domain?

    __tablename__ = 'vm'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=255), nullable=False)
    pool_id = db.Column(UUID(), db.ForeignKey('pool.id', ondelete="CASCADE"), unique=False)
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    created_by_vdi = db.Column(db.Boolean(), nullable=False, default=False)
    broken = db.Column(db.Boolean(), nullable=False, default=False)

    @property
    def entity_type(self):
        return EntityType.VM

    @property
    def entity(self):
        return {'entity_type': self.entity_type, 'entity_uuid': self.id}

    @property
    async def entity_obj(self):
        return await Entity.query.where(
            (Entity.entity_type == self.entity_type) & (Entity.entity_uuid == self.id)).gino.first()

    @property
    def controller_query(self):
        from controller.models import Controller
        from pool.models import Pool
        return db.select([Controller.address]).select_from(
            Controller.join(Pool.query.where(Pool.id == self.pool_id).alias()).alias())

    @property
    async def controller_address(self):
        return await self.controller_query.gino.scalar()

    @property
    async def username(self):
        entity_query = Entity.select('id').where((Entity.entity_type == EntityType.VM) & (Entity.entity_uuid == self.id))
        ero_query = EntityRoleOwner.select('user_id').where(EntityRoleOwner.entity_id == entity_query)
        user_id = await ero_query.gino.scalar()
        user = await User.get(user_id) if user_id else None
        return user.username if user else None

    # ----- ----- ----- ----- ----- ----- -----

    @classmethod
    async def create(cls, pool_id, template_id, verbose_name, id=None,
                     created_by_vdi=False, broken=False):
        log.debug(_('Create VM {} on VDI DB.').format(verbose_name))
        try:
            vm = await super().create(id=id,
                                      pool_id=pool_id,
                                      template_id=template_id,
                                      verbose_name=verbose_name,
                                      created_by_vdi=created_by_vdi,
                                      broken=broken)
        except Exception as E:
            raise VmCreationError(E)

        await log.info(_('VM {} is created').format(verbose_name))

        return vm

    async def soft_delete(self, dest):
        log.debug('Calling soft delete for vm {}'.format(self.verbose_name))
        if self.created_by_vdi:
            controller_address = await self.controller_address
            if controller_address:
                vm_http_client = await VmHttpClient.create(controller_address, self.id)
                try:
                    await vm_http_client.remove_vm()
                except HttpError as http_error:
                    await log.warning(_('Fail to remove VM {} from ECP: ').format(self.verbose_name, http_error))
                log.debug(_('Vm {} removed from ECP.').format(self.verbose_name))

        try:
            await self.delete()
            msg = _('{} {} had remove.').format(dest, self.verbose_name)
            if self.entity:
                await log.info(msg, entity_dict=self.entity)
            else:
                await log.info(msg)
            return True
        except Exception as ex:
            log.debug(_('Soft_delete exception: {}').format(ex))
            return False

    # TODO: очевидное дублирование однотипного кода. Переселить это все в универсальный метод
    async def add_user(self, user_id):
        entity = await self.entity_obj
        try:
            async with db.transaction():
                if not entity:
                    entity = await Entity.create(**self.entity)
                ero = await EntityRoleOwner.create(entity_id=entity.id, user_id=user_id)
                user = await User.get(user_id)
                await log.info(_('User {} is added to VM {}').format(user.username, self.verbose_name))
        except UniqueViolationError:
            raise SimpleError(_('Vm already has permission.'))
        return ero

    async def add_users(self, users_list: list):
        for user_id in users_list:
            await self.add_user(user_id)
        return True

    async def remove_users(self, users_list: list):
        entity = Entity.select('id').where((Entity.entity_type == self.entity_type) & (Entity.entity_uuid == self.id))
        # TODO: временное решение. Скорее всего потом права отзываться будут на конкретные сущности
        await log.info(_('VM {} is clear from users').format(self.verbose_name))
        if not users_list:
            return await EntityRoleOwner.delete.where(EntityRoleOwner.entity_id == entity).gino.status()
        return await EntityRoleOwner.delete.where(
            (EntityRoleOwner.user_id.in_(users_list)) & (EntityRoleOwner.entity_id == entity)).gino.status()

    @staticmethod
    async def get_vm_id(pool_id, user_id):
        entity_query = Entity.select('entity_uuid').where(
            (Entity.entity_type == EntityType.VM) & (
                Entity.id.in_(EntityRoleOwner.select('entity_id').where(EntityRoleOwner.user_id == user_id))))
        vm_query = Vm.select('id').where((Vm.id.in_(entity_query)) & (Vm.pool_id == pool_id))
        return await vm_query.gino.scalar()

    @staticmethod
    async def get_all_vms_ids():
        # TODO: какой-то бесполезный метод
        return await get_list_of_values_from_db(Vm, Vm.id)

    @staticmethod
    async def get_vms_ids_in_pool(pool_id):
        """Get all vm_ids as list of strings"""
        vm_ids_data = await Vm.select('id').where((Vm.pool_id == pool_id)).gino.all()
        vm_ids = [str(vm_id) for (vm_id,) in vm_ids_data]
        return vm_ids

    @staticmethod
    def ready_to_connect(**info) -> bool:
        """Checks parameters indicating availability for connection."""
        power_state = info.get('user_power_state', 0)
        remote_access = info.get('remote_access', False)
        return power_state != 3 or not remote_access

    @staticmethod
    async def copy(verbose_name: str, domain_id: str, datapool_id: str, controller_ip: str,
                   node_id: str, create_thin_clones: bool, domain_index: int):
        """Copy existing VM template for new VM create."""

        client = await VmHttpClient.create(controller_ip, domain_id, verbose_name)

        inner_retry_count = 0
        while True:
            log.debug('Сreating VM {}. Try num: {}'.format(verbose_name, inner_retry_count))

            try:
                response = await client.copy_vm(node_id=node_id,
                                                datapool_id=datapool_id,
                                                domain_name=verbose_name,
                                                create_thin_clones=create_thin_clones)
                break
            except BadRequest as http_error:
                ecp_errors = http_error.errors.get('errors')
                ecp_detail_l = ecp_errors.get('detail') if ecp_errors and isinstance(ecp_errors, dict) else None
                ecp_detail_l = ecp_errors if not ecp_detail_l and isinstance(ecp_errors, list) else ecp_detail_l
                ecp_detail = ecp_detail_l[0] if isinstance(ecp_detail_l, list) else None
                log.debug('ECP error: {}'.format(ecp_errors))

                if ecp_errors and 'verbose_name' in ecp_errors:
                    # deprecated in 2.1 - начиная с 4.3 подбор имени делается контроллером.
                    log.debug('Bad domain name {}'.format(verbose_name))
                    domain_index_old = domain_index
                    domain_index = domain_index + 1
                    verbose_name = re.sub(r'-{}$'.format(domain_index_old), '-{}'.format(domain_index), verbose_name)
                elif ecp_detail and 'not enough free space on data pool' in ecp_detail:
                    # await log.warning(_('Controller has not free space for creating new VM.'))
                    raise VmCreationError(_('Not enough free space on data pool'))
                elif ecp_detail and 'passed node is not valid' in ecp_detail:
                    # await log.warning(_('Unknown node {}').format(node_id))
                    raise VmCreationError(_('Controller can\'t create VM. Unknown node.'))
                elif ecp_detail and 'copy not zfs disks with snapshots to zfs pool' in ecp_detail:
                    raise VmCreationError(
                        _('Controller can\'t create VM. Copy not zfs disks with snapshot to zfs pool'))
                elif ecp_errors and ecp_detail and inner_retry_count < 30:
                    # Тут мы предполагаем, что контроллер заблокирован выполнением задачи. Это может быть и не так,
                    # но сейчас нам это не понятно.
                    log.debug('Possibly blocked by active task on ECP. Wait before next try.')
                    await asyncio.sleep(10)
                else:
                    raise BadRequest(http_error)
            except ServerError as server_error:
                log.debug('ECP error: {}'.format(server_error))
                raise VmCreationError(_('Controller can\'t process request. See VeiL ECP logs.'))

            inner_retry_count += 1
            await asyncio.sleep(1)

        copy_result = dict(id=response['entity'],
                           task_id=response['_task']['id'],
                           verbose_name=verbose_name,
                           domain_index=domain_index)
        return copy_result

    @staticmethod
    async def remove_vms(vm_ids):
        """Remove given vms"""
        for vm_id in vm_ids:
            vm = await Vm.get(vm_id)
            status = await vm.soft_delete(dest=_('VM'))
            await log.info(_('Vm {} removed from pool').format(vm.verbose_name))
        return status

    @staticmethod
    async def enable_remote_access(controller_address, vm_id):
        vm_http_client = await VmHttpClient.create(controller_address, vm_id)
        remote_access_enabled = await vm_http_client.remote_access_enabled()
        if not remote_access_enabled:
            await vm_http_client.enable_remote_access()

    @staticmethod
    async def enable_remote_accesses(controller_address, vm_ids):
        async_tasks = [
            Vm.enable_remote_access(controller_address=controller_address, vm_id=vm_id)
            for vm_id in vm_ids
        ]
        await tornado.gen.multi(async_tasks)

    @staticmethod
    async def get_template_os_type(controller_address, template_id):
        vm_http_client = await VmHttpClient.create(controller_address, template_id)
        domain_info = await vm_http_client.info()
        return domain_info['os_type'] if domain_info else None
