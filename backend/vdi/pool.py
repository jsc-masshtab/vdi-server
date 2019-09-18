import asyncio
#from dataclasses import dataclass
import uuid

from cached_property import cached_property as cached
from db.db import db
from vdi.tasks import vm
from vdi.utils import into_words

#@dataclass()
class Pool:
    params = dict()

    def __init__(self, params: dict):
        self.params = params

    pool_keys = into_words('id name controller_ip desktop_pool_type '
                           'deleted datapool_id cluster_id node_id vm_name_template '
                           'initial_size reserve_size total_size')

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
            qu = """
            insert into vm (id, pool_id, template_id) values ($1, $2, $3)
            """, domain_id, self.params['id'], template['id']
            await conn.execute(*qu)

    async def on_vm_taken(self):
        reserve_size = self.params['reserve_size']
        # Check that total_size is not reached
        num = await self._get_vm_amount_in_pool()
        if num >= self.params['total_size']:
            return
        if reserve_size > len(self.queue._queue):
            self.add_domain(num + 1)

    def add_domain(self, domain_index):
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
        task = vm.CopyDomain(**params).task
        return task

    async def add_domains(self):
        initial_size = self.params['initial_size']
        domains = []

        delta = initial_size - len(self.queue._queue)
        if delta < 0:
            delta = 0

        vm_amount = await self._get_vm_amount_in_pool()
        for i in range(delta):
            domain_index = vm_amount + 1 + i
            d = await self.add_domain(domain_index)
            await self.on_vm_created(d)
            domains.append(d)

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

    @classmethod
    async def get_pool(cls, pool_id):
        if pool_id in cls.instances:
            return cls.instances[pool_id]
        async with db.connect() as conn:
            qu = "SELECT * from pool where id = $1", pool_id
            data = await conn.fetch(*qu)
        if not data:
            return None
        [params] = data

        # dynamic traits!!
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

    async def _get_vm_amount_in_pool(self):
        async with db.connect() as conn:
            qu = "select count(*) from vm where pool_id = $1", self.params['id']
            [(num,)] = await conn.fetch(*qu)
        return num

    instances = {}

    # TODO from_db
    # TODO any created vm -> db

# pool = Pool()

