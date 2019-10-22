import asyncio
import uuid

from cached_property import cached_property as cached
from db.db import db
from vdi.tasks import vm
from vdi.utils import into_words

from vdi.errors import BadRequest, VmCreationError

from vdi.resources_monitoring.subscriptions_observers import WaiterSubscriptionObserver
from vdi.resources_monitoring.resources_monitor_manager import resources_monitor_manager
from vdi.resources_monitoring.resources_monitoring_data import VDI_TASKS_SUBSCRIPTION

from vdi.utils import cancel_async_task


class PoolObject:
    def __init__(self, params: dict):
        self.params = params
        self.write_lock = asyncio.Lock()  # for protection from simultaneous change
        self.add_initial_vms_task = None
        self.current_vm_task_id = None

    def update_param(self, key, value):
        if key in self.params:
            self.params[key] = value

    async def expand_pool_if_requred(self):
        """
        Check and expand pool if required
        :return:
        """
        # Check that total_size is not reached
        vm_amount_in_pool = await PoolObject.get_vm_amount_in_pool(self.params['id'])
        # If reached then do nothing
        if vm_amount_in_pool >= self.params['total_size']:
            return

        amount_of_added_vms = 5  # число машин добавляемых за раз, когда требуется расширение пула (если возможно)
        # reserve_size - желаемое минимальное количество подогретых машин (добавленных в пул, но не имеющих пользоватля)
        # Число машин в пуле, неимеющих пользователя
        free_vm_amount = await PoolObject.get_vm_amount_in_pool(self.params['id'], True)
        # Если подогретых машин слишком мало, то пробуем добавить еще
        if free_vm_amount < self.params['reserve_size']:
            # Max possible amount of VMs which we can add to the pool
            max_possible_amount_to_add = self.params['total_size'] - vm_amount_in_pool
            # Real amount that we can add to the pool
            real_amount_to_add = min(max_possible_amount_to_add, amount_of_added_vms)
            # add VMs.
            try:
                for i in range(real_amount_to_add):
                    domain_index = vm_amount_in_pool + 1 + i
                    await self.add_domain(domain_index)
            except VmCreationError:
                # log that we cant expand the pool.  Mark pool as broken?
                pass

    async def add_domain(self, domain_index):
        """
        Try to add VM to pool
        :param domain_index:
        :return:
        """
        from vdi.tasks import vm
        vm_name_template = (self.params['vm_name_template'] or self.params['name'])
        uid = str(uuid.uuid4())[:7]

        params = {
            'verbose_name': "{}-{}-{}".format(vm_name_template, domain_index, uid),
            'name_template': vm_name_template,
            'domain_id': self.params['template_id'],
            'datapool_id': self.params['datapool_id'],
            'controller_ip': self.params['controller_ip'],
            'node_id': self.params['node_id'],
        }

        MAX_AMOUNT_OF_CREATE_ATTEMPTS = 2

        # try to create vm
        for i in range(MAX_AMOUNT_OF_CREATE_ATTEMPTS):
            print('add_domain № {}, attempt № {}'.format(domain_index, i))
            # send request to create vm
            try:
                vm_info = await vm.CopyDomain(**params).task
                self.current_vm_task_id = vm_info['task_id']
            except BadRequest:  # network or controller problems
                print('BadRequest')
                continue

            # subscribe to ws messages
            response_waiter = WaiterSubscriptionObserver()
            response_waiter.add_subscription_source('/tasks/')

            resources_monitor_manager.subscribe(response_waiter)
            # wait for result
            MAX_TIME_TO_WAIT = 12
            is_vm_successfully_created = await response_waiter.wait_for_message(
                self._check_if_vm_created, MAX_TIME_TO_WAIT)
            resources_monitor_manager.unsubscribe(response_waiter)

            print('is_vm_successfully_created', is_vm_successfully_created)
            if is_vm_successfully_created:
                await self._add_vm_to_db(vm_info, self.params['template_id'])
                return vm_info
            else:
                continue  # go to try again

        raise VmCreationError('Cant create VM')

    async def add_initial_vms(self):
        """
        Create required initial amount of VMs for auto pool
        :return:
        """

        # # fetch_template_info
        # template_info = await GetDomainInfo(controller_ip=pool_args_dict['controller_ip'],
        #                                     domain_id=pool_args_dict['template_id'])

        initial_size = self.params['initial_size']
        domains = []
        try:
            for i in range(initial_size):
                domain_index = 1 + i
                domain = await self.add_domain(domain_index)
                domains.append(domain)

                # notify VDI front about progress(WS)
                msg = 'Automated pool creation. Created {} VMs from {}'.format(domain_index, initial_size)
                msg_dict = {'msg': msg, 'msg_type': 'data', 'event': 'pool_creation_progress',
                            'pool_id': self.params['id'], 'domain_index': domain_index, 'initial_size': initial_size,
                            'resource': VDI_TASKS_SUBSCRIPTION}
                resources_monitor_manager.signal_internal_event(msg_dict)
        except VmCreationError:
            # log that we cant create required initial amount of VMs
            print('Cant create VM')

        # notify VDI front about pool creation result (WS)
        is_creation_successful = (len(domains) == initial_size)
        if is_creation_successful:
            msg = 'Automated pool successfully created. Initial VM amount {}'.format(len(domains))
        else:
            msg = 'Automated pool created with errors. VMs created: {}. Required: {}'.\
                format(len(domains), initial_size)
        msg_dict = {'msg': msg, 'msg_type': 'data', 'event': 'pool_creation_completed',
                    'pool_id': self.params['id'], 'amount_of_created_vms': len(domains), 'initial_size': initial_size,
                    'is_successful': is_creation_successful, 'resource': VDI_TASKS_SUBSCRIPTION}
        resources_monitor_manager.signal_internal_event(msg_dict)

    async def load_vms(self):
        vms = await vm.ListVms(controller_ip=self.params['controller_ip'])
        valid_ids = {v['id'] for v in vms}
        qu = "SELECT * FROM vm WHERE pool_id = $1", self.params['id']
        async with db.connect() as conn:
            vms = await conn.fetch(*qu)
        return [
            dict(v.items()) for v in vms if v['id'] in valid_ids
        ]

    @staticmethod
    async def get_vm_amount_in_pool(pool_id, only_free=False):
        async with db.connect() as conn:
            if only_free:
                qu = "select count(*) from vm where pool_id = $1 AND username is NULL", pool_id
            else:
                qu = "select count(*) from vm where pool_id = $1", pool_id
            [(num,)] = await conn.fetch(*qu)
        return num

    @staticmethod
    async def get_user_amount_in_pool(pool_id):
        async with db.connect() as conn:
            qu = """
            SELECT count(*) 
            FROM pools_users JOIN public.user as u ON pools_users.username = u.username
            WHERE pool_id = {}
            """.format(pool_id)
            [(num,)] = await conn.fetch(qu)
        return num

    # PRIVATE METHODS
    @staticmethod
    def _is_vm_creation_task(name):
        """
        Determine domain creation task by name
        """
        if name.startswith('Создание виртуальной машины'):
            return True
        if all(word in name.lower() for word in ['creating', 'virtual', 'machine']):
            return True
        return False

    def _check_if_vm_created(self, json_message):
        #print('json_message', json_message)
        obj = json_message['object']
        if PoolObject._is_vm_creation_task(obj['name']) and self.current_vm_task_id == obj['parent']:
            if obj['status'] == 'SUCCESS':
                return True
        return False

    async def _add_vm_to_db(self, result, template_id):
        domain_id = result['id']
        # insert into db
        async with db.connect() as conn:
            qu = """
            insert into vm (id, pool_id, template_id) values ($1, $2, $3)
            """, domain_id, self.params['id'], template_id
            await conn.execute(*qu)


class AutomatedPoolManager:

    pool_keys = into_words('id name controller_ip desktop_pool_type '
                           'deleted datapool_id cluster_id node_id template_id vm_name_template '
                           'initial_size reserve_size total_size')

    pool_instances = {}

    @classmethod
    async def get_pool(cls, pool_id):
        if pool_id in cls.pool_instances:
            return cls.pool_instances[pool_id]
        async with db.connect() as conn:
            qu = "SELECT * from pool where id = $1", pool_id
            data = await conn.fetch(*qu)
        if not data:
            return None
        [params] = data

        ins = PoolObject(params=params)
        cls.pool_instances[pool_id] = ins
        return ins

    @classmethod
    async def wake_pool(cls, pool_id):
        ins = await cls.get_pool(pool_id)
        return ins
