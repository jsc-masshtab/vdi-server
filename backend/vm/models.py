# -*- coding: utf-8 -*-
import uuid
import logging
import re
import asyncio

from sqlalchemy.dialects.postgresql import UUID
import tornado.gen

from database import db, get_list_of_values_from_db, AbstractEntity
from common.veil_errors import BadRequest, HttpError, VmCreationError
from vm.veil_client import VmHttpClient

application_log = logging.getLogger('tornado.application')


class Vm(db.Model, AbstractEntity):
    # TODO: положить в таблицу данные о удаленном подключении из ECP

    ACTIONS = ('start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot')
    POWER_STATES = ('unknown', 'power off', 'power on and suspended', 'power on')

    __tablename__ = 'vm'

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=255), nullable=False)
    pool_id = db.Column(UUID(), db.ForeignKey('pool.id', ondelete="CASCADE"), unique=False)
    username = db.Column(db.Unicode(length=100))  # TODO: change to user.id
    template_id = db.Column(db.Unicode(length=100), nullable=True)

    # TODO: ip address of domain
    # TODO: port of domain

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__created_by_vdi = None
        self.__controller_address = None

    # ----- ----- ----- ----- ----- ----- -----
    # Properties:

    @property
    def created_by_vdi(self):
        """Признак указывающий, что мы можем удалять domain на ECP."""
        return self.__created_by_vdi

    @created_by_vdi.setter
    def created_by_vdi(self, b: bool):
        self.__created_by_vdi = b if isinstance(b, bool) else None

    @property
    def controller_address(self):
        return self.__controller_address

    @controller_address.setter
    def controller_address(self, ip: str):
        self.__controller_address = ip

    # ----- ----- ----- ----- ----- ----- -----

    @classmethod
    async def create(cls, pool_id, template_id, controller_address, created_by_vdi, verbose_name, id=None,
                     username=None):
        # TODO: убедиться, что если в create не передан id присвоится значение по-умолчанию
        application_log.debug('Create VM {} on VDI DB.'.format(verbose_name))
        try:
            vm = await super().create(id=id,
                                      pool_id=pool_id,
                                      username=username,
                                      template_id=template_id,
                                      verbose_name=verbose_name)
        except Exception as E:
            application_log.error(E)
            raise VmCreationError('Can\'t create VM')
        # Set properties
        setattr(vm, 'created_by_vdi', created_by_vdi)
        setattr(vm, 'controller_address', controller_address)
        application_log.debug('VM {} properties are set.'.format(verbose_name))
        return vm

    async def soft_delete(self):
        if self.created_by_vdi:
            vm_http_client = await VmHttpClient.create(self.controller_address, self.id)
            try:
                application_log.info('Starting remove VM {} from ECP.'.format(self.verbose_name))
                await vm_http_client.remove_vm()
            except HttpError as http_error:
                application_log.warning('Fail to remove VM {} from ECP. '.format(self.verbose_name))
                application_log.debug(http_error)
            application_log.debug('Vm {} removed from ECP.'.format(self.verbose_name))
        return await self.delete()

    @staticmethod
    def domain_name(verbose_name: str, name_template: str):
        if verbose_name:
            return verbose_name
        return '{}-1'.format(name_template)

    @staticmethod
    async def attach_vm_to_user(vm_id, username):
        return await Vm.update.values(username=username).where(
            Vm.id == vm_id).gino.status()

    async def free_vm(self):
        return await self.update(username=None).apply()

    @staticmethod
    async def get_vm_id(pool_id, username):
        return await Vm.select('id').where((Vm.username == username) & (Vm.pool_id == pool_id)).gino.scalar()

    @staticmethod
    async def get_template_id(vm_id):
        return await Vm.select('template_id').where((Vm.id == vm_id)).gino.scalar()

    @staticmethod
    async def get_pool_id(vm_id):
        return await Vm.select('pool_id').where((Vm.id == vm_id)).gino.scalar()

    @staticmethod
    async def get_username(vm_id):
        return await Vm.select('username').where((Vm.id == vm_id)).gino.scalar()

    @staticmethod
    async def get_all_vms_ids():
        return await get_list_of_values_from_db(Vm, Vm.id)

    @staticmethod
    async def get_vms_ids_in_pool(pool_id):
        """Get all vm_ids as list of strings"""
        vm_ids_data = await Vm.select('id').where((Vm.pool_id == pool_id)).gino.all()
        vm_ids = [str(vm_id) for (vm_id,) in vm_ids_data]
        return vm_ids

    @staticmethod
    async def get_free_vm_id_from_pool(pool_id):
        """Get fee vm"""
        res = await Vm.select('id').where(((Vm.username == None) & (Vm.pool_id == pool_id))).gino.first()
        if res:
            (vm_id, ) = res
            return vm_id
        else:
            return None

    @staticmethod
    def ready_to_connect(**info) -> bool:
        """Checks parameters indicating availability for connection."""
        power_state = info.get('user_power_state', 0)
        remote_access = info.get('remote_access', False)
        return power_state != 3 or not remote_access

    @staticmethod
    async def copy(verbose_name: str, name_template: str, domain_id: str, datapool_id: str, controller_ip: str,
                   node_id: str, create_thin_clones: bool, domain_index: int):
        """Copy existing VM template for new VM create."""

        domain_name = Vm.domain_name(verbose_name=verbose_name, name_template=name_template)
        application_log.debug(
            'VmHttpClient: controller_ip: {}, domain_id: {}, verbose_name: {}, name_template: {}'.format(controller_ip,
                                                                                                         domain_id,
                                                                                                         verbose_name,
                                                                                                         name_template))
        client = await VmHttpClient.create(controller_ip, domain_id, verbose_name, name_template)
        inner_retry_count = 0
        while True:
            inner_retry_count += 1
            try:
                application_log.info(
                    'Trying to create VM on ECP with verbose_name={} and domain_name={}'.format(verbose_name,
                                                                                                domain_name))
                application_log.debug('Подождем перед попыткой создать новую VM')
                await asyncio.sleep(1)
                response = await client.copy_vm(node_id=node_id, datapool_id=datapool_id, domain_name=domain_name,
                                                create_thin_clones=create_thin_clones)
            except BadRequest as http_error:
                ecp_errors = http_error.errors.get('errors')
                application_log.debug(http_error)
                if ecp_errors and 'verbose_name' in ecp_errors:
                    application_log.warning('Bad domain name {}'.format(domain_name))
                    domain_index_old = domain_index
                    domain_index = domain_index + 1
                    verbose_name = re.sub(r'-{}$'.format(domain_index_old), '-{}'.format(domain_index), verbose_name)
                    domain_name = verbose_name
                elif ecp_errors and 'detail' in ecp_errors and inner_retry_count < 30:
                    # TODO: это очень странное условие, наверняка от него откажемся
                    application_log.warning('Possibly blocked by active task on ECP.')
                    application_log.debug(http_error)
                    application_log.debug('Подождем подольше перед повторной попыткой.')
                    await asyncio.sleep(10)
                else:
                    application_log.debug('Unknown exception. Break.')
                    application_log.debug(ecp_errors)
                    raise BadRequest(http_error)
            else:
                application_log.debug('No ex. Break')
                break
        copy_result = dict(id=response['entity'],
                           task_id=response['_task']['id'],
                           verbose_name=domain_name,
                           domain_index=domain_index)
        application_log.debug(copy_result)
        return copy_result

    @staticmethod
    async def remove_vms(vm_ids):
        """Remove given vms"""
        for vm_id in vm_ids:
            vm = await Vm.get(vm_id)
            await vm.soft_delete()
        return True

    @staticmethod
    async def enable_remote_access(controller_address, vm_id):
        vm_http_client = await VmHttpClient.create(controller_address, vm_id)
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
