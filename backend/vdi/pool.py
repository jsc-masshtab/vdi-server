import asyncio
#from dataclasses import dataclass
import uuid

from cached_property import cached_property as cached
from db.db import db
from vdi.tasks import vm
from vdi.utils import into_words


class PoolObject:
    def __init__(self, params: dict):
        self.params = params
        self.write_lock = asyncio.Lock()  # for protection from simultaneous change

    async def on_vm_created(self, result):
        domain_id = result['id']
        template = result['template']
        # insert into db
        async with db.connect() as conn:
            qu = """
            insert into vm (id, pool_id, template_id) values ($1, $2, $3)
            """, domain_id, self.params['id'], template['id']
            await conn.execute(*qu)

    async def on_vm_taken(self):
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
            for i in range(real_amount_to_add):
                domain_index = vm_amount_in_pool + 1 + i
                await self.add_domain(domain_index)

    async def add_domain(self, domain_index):
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
        info = await vm.CopyDomain(**params).task
        await self.on_vm_created(info)
        return info

    async def add_domains(self):
        initial_size = self.params['initial_size']
        domains = []

        vm_amount = await AutomatedPoolManager.get_vm_amount_in_pool(self.params['id'])
        delta = initial_size - vm_amount
        if delta < 0:
            delta = 0

        for i in range(delta):
            domain_index = vm_amount + 1 + i
            domain = await self.add_domain(domain_index)
            domains.append(domain)

        return domains

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
