import json
import uuid

import asyncio
from .utils import callback
from .context_utils import enter_context

from classy_async import g, wait

from dataclasses import dataclass

from cached_property import cached_property as cached

from vdi.db import db
from vdi.tasks import vm
from asyncpg.connection import Connection

@dataclass()
class Pool:
    params: dict


    @cached
    def queue(self):
        return asyncio.Queue()

    @cached
    def tasks(self):
        'TODO'

    @callback
    @enter_context(lambda: db.connect())
    async def on_vm_created(conn: Connection, self, fut):
        if fut.exception():
            # FIXME
            print(fut.exception())
            return
        result = fut.result()
        domain_id = result['id']
        template = result['template']
        await self.queue.put(result)
        # insert into db
        qu = f"""
        insert into vm (id, pool_id, template_id, state) values ($1, $2, $3, $4)
        """, domain_id, self.params['id'], template['id'], 'queued'
        await conn.execute(*qu)

    def on_vm_taken(self):
        initial_size = self.params['initial_size']
        if initial_size > len(self.queue._queue):
            self.add_domain()

    def add_domain(self):
        from vdi.tasks import vm
        g.init()
        params = {
            'name_template': self.params['name'],
            'domain_id': self.params['template_id'],
            'datapool_id': self.params['datapool_id'],
            'controller_ip': self.params['controller_ip'],
            'node_id': self.params['node_id'],
        }
        task = vm.CopyDomain(**params).task
        task.add_done_callback(self.on_vm_created)
        return task

    async def add_domains(self):
        initial_size = self.params['initial_size']
        domains = []

        delta = initial_size - len(self.queue._queue)
        if delta < 0:
            delta = 0

        for i in range(delta):
            d = await self.add_domain()
            domains.append(d)

        return domains

    async def load_vms(self, conn):
        vms = await vm.ListVms(controller_ip=self.params['controller_ip'])
        valid_ids = {v['id'] for v in vms}
        qu = f"SELECT * FROM vm WHERE pool_id = $1", self.params['id']
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


    @enter_context(lambda: db.connect())
    async def init(conn, self, id, add_missing=False):
        """
        Init the pool (possibly, after service restart)
        """
        assert not len(self.queue._queue)
        vms = await self.load_vms(conn)

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

