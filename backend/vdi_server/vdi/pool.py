import asyncio
from dataclasses import dataclass

from cached_property import cached_property as cached
from vdi.db import db
from vdi.tasks import vm


@dataclass()
class Pool:
    params: dict

    #FIXME use queue only for client


    @cached
    def queue(self):
        return asyncio.Queue()

    @cached
    def tasks(self):
        'TODO'

    async def on_vm_created(self, result):
        domain_id = result['id']
        template = result['template']
        await self.queue.put(result)
        # insert into db
        async with db.connect() as conn:
            qu = f"""
            insert into vm (id, pool_id, template_id) values ($1, $2, $3)
            """, domain_id, self.params['id'], template['id']
            await conn.execute(*qu)

    async def on_vm_taken(self):
        reserve_size = self.params['reserve_size']
        # Check that total_size is not reached
        async with db.connect() as conn:
            qu = f"select from count(vm.id) where pool_id = $1", self.params['id']
            [(num,)] = await conn.fetch(*qu)
            if num >= self.params['total_size']:
                return
        if reserve_size > len(self.queue._queue):
            self.add_domain()

    def add_domain(self):
        from vdi.tasks import vm
        params = {
            'name_template': self.params['name'],
            'domain_id': self.params['template_id'],
            'datapool_id': self.params['datapool_id'],
            'controller_ip': self.params['controller_ip'],
            'node_id': self.params['node_id'],
        }
        task = vm.CopyDomain(**params).task
        return task

    async def add_domains(self):
        initial_size = self.params['initial_size']
        domains = []

        delta = initial_size - len(self.queue._queue)
        if delta < 0:
            delta = 0

        for i in range(delta):
            d = await self.add_domain()
            await self.on_vm_created(d)
            domains.append(d)

        return domains

    async def load_vms(self):
        vms = await vm.ListVms(controller_ip=self.params['controller_ip'])
        valid_ids = {v['id'] for v in vms}
        qu = f"SELECT * FROM vm WHERE pool_id = $1", self.params['id']
        async with db.connect() as conn:
            vms = await conn.fetch(*qu)
        return [
            dict(v.items()) for v in vms if v['id'] in valid_ids
        ]

    @classmethod
    async def get_pool(cls, pool_id):
        if pool_id in cls.instances:
            return cls.instances[pool_id]
        async with db.connect() as conn:
            qu = f"SELECT * from pool where id = $1", pool_id
            [params] = await conn.fetch(*qu)
            ins = cls(params=params)
            cls.instances[pool_id] = ins
            return ins


    async def init(self, id, add_missing=False):
        """
        Init the pool (possibly, after service restart)
        """
        assert not len(self.queue._queue)
        vms = await self.load_vms()

        for vm in vms:
            await self.queue.put(vm)

        add_domains = self.add_domains()
        if add_missing:
            await add_domains

    @classmethod
    async def wake_pool(cls, pool_id):
        ins = await cls.get_pool(pool_id)
        await ins.init(pool_id)
        return ins

    instances = {}

    # TODO from_db
    # TODO any created vm -> db

# pool = Pool()

