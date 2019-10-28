# -*- coding: utf-8 -*-
from database import db
from vm.models import Vm
from common.veil_errors import VmCreationError, BadRequest

from resources_monitoring.subscriptions_observers import WaiterSubscriptionObserver
from resources_monitoring.resources_monitor_manager import resources_monitor_manager


class Pool(db.Model):
    MIX_POOL_SIZE = 1
    MAX_POOL_SIZE = 200
    MAX_VM_AMOUNT_IN_POOL = 1000
    VM_STEP = 5
    MAX_AMOUNT_OF_CREATE_ATTEMPTS = 2

    __tablename__ = 'pool'
    id = db.Column(db.Integer(), nullable=False, autoincrement=True, primary_key=True)
    name = db.Column(db.Unicode(length=255), nullable=False)
    controller_ip = db.Column(db.Unicode(length=255), nullable=False)
    desktop_pool_type = db.Column(db.Unicode(length=255), nullable=False)

    deleted = db.Column(db.Boolean())
    dynamic_traits = db.Column(db.Integer(), nullable=True)  # remove it

    datapool_id = db.Column(db.Unicode(length=100), nullable=True)
    cluster_id = db.Column(db.Unicode(length=100), nullable=True)
    node_id = db.Column(db.Unicode(length=100), nullable=True)
    template_id = db.Column(db.Unicode(length=100), nullable=True)

    initial_size = db.Column(db.Integer(), nullable=True)
    reserve_size = db.Column(db.Integer(), nullable=True)  # желаемое минимальное количествиюво подогретых машин
                                                           # (добавленных в пул, но не имеющих пользоватля)
    total_size = db.Column(db.Integer(), nullable=False, default=MIX_POOL_SIZE)
    vm_name_template = db.Column(db.Unicode(length=100), nullable=True)

    @staticmethod
    async def get_pool(pool_id):
        """Return pool object if exist"""
        return await Pool.get(pool_id)

    async def get_vm_amount(self, only_free=False):
        """ == None because alchemy can't work with is None"""
        if only_free:
            return await db.select([db.func.count()]).where(
                (Vm.pool_id == self.id) & (Vm.username == None)).gino.scalar()  # noqa
        else:
            return await db.select([db.func.count()]).where(Vm.pool_id == self.id).gino.scalar()

    async def add_vm(self, domain_index):
        """
        Try to add VM to pool
        :param domain_index:
        :return:
        """
        # TODO: beautify
        import uuid
        vm_name_template = self.vm_name_template or self.name

        uid = str(uuid.uuid4())[:7]

        params = {
            'verbose_name': "{}-{}-{}".format(vm_name_template, domain_index, uid),
            'name_template': vm_name_template,
            'domain_id': self.template_id,
            'datapool_id': self.datapool_id,
            'controller_ip': self.controller_ip,
            'node_id': self.node_id,
        }

        # try to create vm
        for i in range(self.MAX_AMOUNT_OF_CREATE_ATTEMPTS):
            print('add_domain № {}, attempt № {}'.format(domain_index, i))
            # send request to create vm
            try:
                vm_info = await Vm.copy(**params)
                current_vm_task_id = vm_info['task_id']
                print('current vm task id is {}'.format(current_vm_task_id))
            except BadRequest:
                print('BadRequest')
                continue

            # TODO: не переписывал. Уточнить у Александра какой план насчет подписки на WS
            # subscribe to ws messages
            response_waiter = WaiterSubscriptionObserver()
            response_waiter.add_subscription_source('/tasks/')

            resources_monitor_manager.subscribe(response_waiter)
            # wait for result
            MAX_TIME_TO_WAIT = 15

            def _is_vm_creation_task(name):
                """
                Determine domain creation task by name
                """
                print('is vm creation task')
                print(name)
                if name.startswith('Создание виртуальной машины'):
                    return True
                if all(word in name.lower() for word in ['creating', 'virtual', 'machine']):
                    return True
                return False

            def _check_if_vm_created(json_message):
                print('check vm is created')
                print(json_message)
                obj = json_message['object']

                if _is_vm_creation_task(obj['name']) and current_vm_task_id == obj['parent']:
                    if obj['status'] == 'SUCCESS':
                        return True
                return False
            print('here')

            is_vm_successfully_created = await response_waiter.wait_for_message(
                _check_if_vm_created, MAX_TIME_TO_WAIT)
            resources_monitor_manager.unsubscribe(response_waiter)

            print('VM successfully created: {}'.format(is_vm_successfully_created))

            if is_vm_successfully_created:
                await Vm.create(id=vm_info['id'], pool_id=self.id, template_id=self.template_id)
                return vm_info
            else:
                continue  # go to try again

        raise VmCreationError('Can\'t create VM')

    async def expand_pool_if_requred(self):
        """
        Check and expand pool if required
        :return:
        """
        # TODO: код перенесен, чтобы работал. Принципиально не перерабатывался.
        # Check that total_size is not reached
        vm_amount_in_pool = await self.get_vm_amount()

        # If reached then do nothing
        if vm_amount_in_pool >= self.total_size:
            return

        # Число машин в пуле, неимеющих пользователя
        free_vm_amount = await self.get_vm_amount(only_free=True)

        # Если подогретых машин слишком мало, то пробуем добавить еще
        if self.reserve_size > free_vm_amount:
            # Max possible amount of VMs which we can add to the pool
            max_possible_amount_to_add = self.total_size - vm_amount_in_pool
            # Real amount that we can add to the pool
            real_amount_to_add = min(max_possible_amount_to_add, self.VM_STEP)
            # add VMs.
            try:
                for i in range(1, real_amount_to_add):  # TODO: ugly as fuck
                    domain_index = vm_amount_in_pool + i
                    await self.add_vm(domain_index)
            except VmCreationError:
                # TODO: log that we cant expand the pool.  Mark pool as broken?
                pass

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
    async def get_user_pool2(pool_id, username):
        return await db.select(Pool, Vm
                               ).select_from(
            Pool.join(Vm, Vm.username == username, isouter=True)
        ).where(
            Pool.id == pool_id).gino.first()
        # return await Pool.query.where((id == pool_id) & (username == username)).gino.first()

    @staticmethod
    async def get_controller(pool_id):
        """SELECT controller_ip FROM pool WHERE pool.id =  $1, pool_id"""
        return await Pool.select('controller_ip').where(Pool.id == pool_id).gino.scalar()


class PoolUsers(db.Model):
    __tablename__ = 'pools_users'
    pool_id = db.Column(db.Integer(), db.ForeignKey('pool.id'))
    username = db.Column(db.Integer(), db.ForeignKey('user.username'))

