# -*- coding: utf-8 -*-
import uuid

from sqlalchemy.dialects.postgresql import UUID

from database import db
from vm.models import Vm


class Pool(db.Model):
    __tablename__ = 'pool'
    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    verbose_name = db.Column(db.Unicode(length=128), nullable=False)
    status = db.Column(db.Unicode(length=128), nullable=False)
    controller = db.Column(UUID(as_uuid=True), db.ForeignKey('controllers.id'))

    desktop_pool_type = db.Column(db.Unicode(length=255), nullable=False)

    deleted = db.Column(db.Boolean())
    dynamic_traits = db.Column(db.Integer(), nullable=True)  # remove it

    datapool_id = db.Column(db.Unicode(length=100), nullable=True)
    cluster_id = db.Column(db.Unicode(length=100), nullable=True)
    node_id = db.Column(db.Unicode(length=100), nullable=True)
    template_id = db.Column(db.Unicode(length=100), nullable=True)

    initial_size = db.Column(db.Integer(), nullable=True)
    reserve_size = db.Column(db.Integer(), nullable=True)
    total_size = db.Column(db.Integer(), nullable=True)
    vm_name_template = db.Column(db.Unicode(length=100), nullable=True)

    @staticmethod
    async def get_pool(pool_id):
        return await Pool.where(id == pool_id).gino.all()

    @staticmethod
    async def get_pools(user='admin'):
        # TODO: rewrite normally
        # pools = await Pool.query.gino.all()
        pools = await Pool.select('id', 'name').gino.all()
        ans = list()
        for pool in pools:
            ans_d = dict()
            ans_d['id'] = pool.id
            ans_d['name'] = pool.name
            ans.append(ans_d)
        return ans

    @staticmethod
    async def get_user_pool(pool_id, username=None):
        """Return first hit"""
        return await db.select(
            [
                Pool.controller_ip,
                Pool.desktop_pool_type,
                Vm.id,
            ]
        ).select_from(
            Pool.join(Vm, Vm.username == username, isouter=True)
        ).where(
            Pool.id == pool_id).gino.first()

    @staticmethod
    async def get_controller(pool_id):
        """SELECT controller_ip FROM pool WHERE pool.id =  $1, pool_id"""
        return await Pool.select('controller_ip').where(Pool.id == pool_id).gino.scalar()


class PoolUsers(db.Model):
    __tablename__ = 'pools_users'
    pool_id = db.Column(UUID(), db.ForeignKey('pool.id'))
    user_id = db.Column(UUID(), db.ForeignKey('user.id'))
