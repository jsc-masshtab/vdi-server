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
    created_by_vdi = db.Column(db.Boolean(), nullable=False, default=False)
    broken = db.Column(db.Boolean(), nullable=False, default=False)

    # TODO: ip address of domain
    # TODO: port of domain

    @property
    def controller_query(self):
        from controller.models import Controller
        from pool.models import Pool
        return db.select([Controller.address]).select_from(
            Controller.join(Pool.query.where(Pool.id == self.pool_id).alias()).alias())

    @property
    async def controller_address(self):
        return await self.controller_query.gino.scalar()

    # ----- ----- ----- ----- ----- ----- -----

    @classmethod
    async def create(cls, pool_id, template_id, verbose_name, id=None,
                     username=None, created_by_vdi=False, broken=False):
        # TODO: убедиться, что если в create не передан id присвоится значение по-умолчанию
        application_log.debug('Create VM {} on VDI DB.'.format(verbose_name))
        try:
            vm = await super().create(id=id,
                                      pool_id=pool_id,
                                      username=username,
                                      template_id=template_id,
                                      verbose_name=verbose_name,
                                      created_by_vdi=created_by_vdi,
                                      broken=broken)
        except Exception as E:
            application_log.error(E)
            raise VmCreationError(E)
        return vm

    async def soft_delete(self):
        application_log.debug('VM {} created by VDI: {}'.format(self.verbose_name, self.created_by_vdi))

        if self.created_by_vdi:
            controller_address = await self.controller_address
            if not controller_address:
                application_log.warning(
                    'There is no controller for AutomatedPool {}. Can\'t delete VMs'.format(self.verbose_name))

            if controller_address:
                vm_http_client = await VmHttpClient.create(controller_address, self.id)
                try:
                    application_log.debug('Starting remove VM {} from ECP.'.format(self.verbose_name))
                    await vm_http_client.remove_vm()
                except HttpError as http_error:
                    application_log.warning('Fail to remove VM {} from ECP. '.format(self.verbose_name))
                    application_log.debug(http_error)
                application_log.debug('Vm {} removed from ECP.'.format(self.verbose_name))
        return await self.delete()

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
        res = await Vm.select('id').where(((Vm.username == None) & (Vm.pool_id == pool_id))).gino.first()  # noqa
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
    async def copy(verbose_name: str, domain_id: str, datapool_id: str, controller_ip: str,
                   node_id: str, create_thin_clones: bool, domain_index: int):
        """Copy existing VM template for new VM create."""

        application_log.debug(
            'VmHttpClient: controller_ip: {}, domain_id: {}, verbose_name: {}'.format(controller_ip,
                                                                                      domain_id,
                                                                                      verbose_name))
        client = await VmHttpClient.create(controller_ip, domain_id, verbose_name)

        inner_retry_count = 0
        while True:
            inner_retry_count += 1
            try:
                application_log.info(
                    'Trying to create VM on ECP with verbose_name={}'.format(verbose_name))

                response = await client.copy_vm(node_id=node_id,
                                                datapool_id=datapool_id,
                                                domain_name=verbose_name,
                                                create_thin_clones=create_thin_clones)
                application_log.debug('Запрос на создание VM отправлен без неожиданностей. Покидаем while.')
                break
            except BadRequest as http_error:
                # TODO: Обработка ошибок это хардкод только для русской версии контроллера. Нужно что-то информативнее.
                ecp_errors = http_error.errors.get('errors')
                ecp_detail_l = ecp_errors.get('detail') if ecp_errors else None
                ecp_detail = ecp_detail_l[0] if isinstance(ecp_detail_l, list) else None
                application_log.debug('ECP error: {}'.format(ecp_errors))
                if ecp_errors and 'verbose_name' in ecp_errors:
                    application_log.warning('Bad domain name {}'.format(verbose_name))
                    domain_index_old = domain_index
                    domain_index = domain_index + 1
                    verbose_name = re.sub(r'-{}$'.format(domain_index_old), '-{}'.format(domain_index), verbose_name)
                elif ecp_errors and ecp_detail and ('недостаточно свободного места на пуле данных' in ecp_detail or 'ot enough free space on data pool' in ecp_detail):
                    application_log.info('На контроллере отсутствует место для создания новой VM.')
                    raise VmCreationError('Недостаточно свободного места на пуле данных.')
                elif ecp_errors and ecp_detail and inner_retry_count < 30:
                    # Тут мы предполагаем, что контроллер заблокирован выполнением задачи. Это может быть и не так,
                    # но сейчас нам это не понятно.
                    application_log.debug('Possibly blocked by active task on ECP. Подождем перед повторной попыткой.')
                    await asyncio.sleep(10)
                else:
                    application_log.debug('Что-то пошло не так. Прерываем while.')
                    application_log.debug(ecp_errors)
                    raise BadRequest(http_error)

            application_log.debug('Нам нужна еще 1 попытка. Подождем.')
            await asyncio.sleep(1)

        copy_result = dict(id=response['entity'],
                           task_id=response['_task']['id'],
                           verbose_name=verbose_name,
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
