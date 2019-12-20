# -*- coding: utf-8 -*-
import uuid
from sqlalchemy.dialects.postgresql import UUID
import tornado.gen

from database import db, get_list_of_values_from_db
from vm.veil_client import VmHttpClient
from event.models import Event

# TODO: сделать схему и методы более осмысленными.


class Vm(db.Model):
    __tablename__ = 'vm'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    pool_id = db.Column(UUID(), db.ForeignKey('pool.pool_id', ondelete="CASCADE"))
    username = db.Column(db.Unicode(length=100))

    ACTIONS = ('start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot')
    POWER_STATES = ('unknown', 'power off', 'power on and suspended', 'power on')

    @staticmethod  # todo: not checked
    async def check_vm_exists(vm_id):
        return await Vm.select().where((Vm.id == vm_id)).gino.all()

    @staticmethod
    def domain_name(verbose_name: str, name_template: str):
        if verbose_name:
            return verbose_name
        uid = str(uuid.uuid4())[:7]
        return '{}-{}'.format(name_template, uid)

    @staticmethod
    async def attach_vm_to_user(vm_id, username):
        return await Vm.update.values(username=username).where(
            Vm.id == vm_id).gino.status()

    # @staticmethod
    # async def free_vm(pool_id, username):
    #     """free vm from user. combination pool_id<->username is unique"""
    #     return await Vm.update.values(username=None).where(
    #         Vm.pool_id == pool_id and Vm.username == username).gino.status()

    @staticmethod
    async def free_vm(vm_id):
        return await Vm.update.values(username=None).where(Vm.id == vm_id).gino.status()

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
                   node_id: str, create_thin_clones: bool):
        """Copy existing VM template for new VM create."""
        # TODO: switch to controller uid?
        domain_name = Vm.domain_name(verbose_name=verbose_name, name_template=name_template)
        client = await VmHttpClient.create(controller_ip, domain_id, verbose_name, name_template)
        response = await client.copy_vm(node_id=node_id, datapool_id=datapool_id, domain_name=domain_name,
                                        create_thin_clones=create_thin_clones)
        return dict(id=response['entity'],
                    task_id=response['_task']['id'],
                    verbose_name=domain_name)

    @staticmethod
    async def remove_vms(vm_ids):
        """Remove given vms"""
        return await Vm.delete.where(Vm.id.in_(vm_ids)).gino.status()

    @staticmethod
    async def remove_vm(controller_ip, vm_id):
        """Удаляет виртуалку на ECP, а потом из БД."""
        vm_http_client = await VmHttpClient.create(controller_ip, vm_id)
        await vm_http_client.remove_vm()
        await Event.create_info('Vm {} removed from ECP.'.format(vm_id))
        return await Vm.delete.where(Vm.id == vm_id).gino.status()

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
        domain_os_type = domain_info['os_type'] if domain_info else None
        return domain_os_type
