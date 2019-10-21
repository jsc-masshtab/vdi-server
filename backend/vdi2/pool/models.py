# -*- coding: utf-8 -*-
from database import db


class Vm(db.Model):
    __tablename__ = 'vm'
    id = db.Column(db.Unicode(length=100), nullable=False)
    template_id = db.Column(db.Unicode(length=100), nullable=True)
    pool_id = db.Column(db.Integer(), db.ForeignKey('pool.id'))
    username = db.Column(db.Unicode(length=100), nullable=False)


class Pool(db.Model):
    __tablename__ = 'pool'
    id = db.Column(db.Integer(), nullable=False, unique=True, autoincrement=True)
    name = db.Column(db.Unicode(length=255), nullable=False)
    controller_ip = db.Column(db.Unicode(length=255), nullable=False)
    desktop_pool_type = db.Column(db.Unicode(length=255), nullable=False)
    deleted = db.Column(db.Boolean())
    dynamic_traits = db.Column(db.Integer(), nullable=True)

    datapool_id = db.Column(db.Unicode(length=100), nullable=True)
    cluster_id = db.Column(db.Unicode(length=100), nullable=True)
    node_id = db.Column(db.Unicode(length=100), nullable=True)
    template_id = db.Column(db.Unicode(length=100), nullable=True)

    initial_size = db.Column(db.Integer(), nullable=True)
    reserve_size = db.Column(db.Integer(), nullable=True)
    total_size = db.Column(db.Integer(), nullable=True)
    vm_name_template = db.Column(db.Unicode(length=100), nullable=True)

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
            # print(ans_d)
            ans.append(ans_d)
        return ans

    @staticmethod
    async def get_user_pools(username='admin', pool_id=28):
        query = await db.select(
            [
                Pool.controller_ip,
                Pool.desktop_pool_type,
                Vm.id,
            ]
            ).select_from(
                Pool.join(Vm)
                ).where((
                    Pool.id == pool_id ) &
                        (Vm.username == username
                )).gino.all()
        return query
