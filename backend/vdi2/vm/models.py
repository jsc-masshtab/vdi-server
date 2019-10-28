# -*- coding: utf-8 -*-
from database import db


class Vm(db.Model):
    __tablename__ = 'vm'
    id = db.Column(db.Unicode(length=100), nullable=False)
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    pool_id = db.Column(db.Integer(), db.ForeignKey('pool.id'))
    username = db.Column(db.Unicode(length=100), nullable=False)

    ACTIONS = ('start', 'suspend', 'reset', 'shutdown', 'resume', 'reboot')
    POWER_STATES = ('unknown', 'power off', 'power on and suspended', 'power on')

    @staticmethod
    async def attach_vm_to_user(vm_id, username):
        return await Vm.update.values(username=username).where(
            Vm.id == vm_id).gino.status()

    @staticmethod
    async def get_vm_id(pool_id, username):
        return await Vm.select('id').where((Vm.username == username) & (Vm.pool_id == pool_id)).gino.scalar()

    @staticmethod
    def ready_to_connect(**info) -> bool:
        """Checks parameters indicating availability for connection."""
        power_state = info.get('user_power_state', 0)
        remote_access = info.get('remote_access', False)
        return power_state != 3 or not remote_access
