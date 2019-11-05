# -*- coding: utf-8 -*-
import uuid
from sqlalchemy.dialects.postgresql import UUID

from database import db, get_list_of_values_from_db
from vm.veil_client import VmHttpClient
# TODO: сделать схему человеческой


class Vm(db.Model):
    __tablename__ = 'vm'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    pool_id = db.Column(UUID(as_uuid=True), db.ForeignKey('pool.id'))
    username = db.Column(db.Unicode(length=100), nullable=False)

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

    @staticmethod
    async def free_vm(pool_id, username):
        """free vm from user. combination pool_id<->username is unique"""
        return await Vm.update.values(username=None).where(
            Vm.pool_id == pool_id and Vm.username == username).gino.status()

    @staticmethod
    async def free_vm(vm_id):
        return await Vm.update.values(username=None).where(Vm.vm_id == vm_id).gino.status()

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
    def ready_to_connect(**info) -> bool:
        """Checks parameters indicating availability for connection."""
        power_state = info.get('user_power_state', 0)
        remote_access = info.get('remote_access', False)
        return power_state != 3 or not remote_access

    @staticmethod
    async def copy(verbose_name: str, name_template: str, domain_id: str, datapool_id: str, controller_ip: str,
                   node_id: str):
        """Copy existing VM template for new VM create."""
        domain_name = Vm.domain_name(verbose_name=verbose_name, name_template=name_template)
        client = VmHttpClient(controller_ip, domain_id, verbose_name, name_template)
        response = await client.copy_vm(node_id=node_id, datapool_id=datapool_id, domain_name=domain_name)
        return dict(id=response['entity'],
                    task_id=response['_task']['id'],
                    verbose_name=domain_name)
