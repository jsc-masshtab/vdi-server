import json
import uuid

import asyncio
from .utils import callback
from .context_utils import enter_context

from classy_async import g

from dataclasses import dataclass

from cached_property import cached_property as cached

from vdi.db import db
from vdi.tasks import vm
from asyncpg.connection import Connection

@dataclass()
class Pool:
    params: dict
    pending: int = 0


    @cached
    def queue(self):
        return asyncio.Queue()

    # TODO make vm info optional?

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
        domain = fut.result()
        await self.queue.put(domain)
        self.queue.task_done()
        self.pending -= 1
        # insert into db
        qu = f"""
        insert into vm (id, pool_id, state) values ($1, $2, $3)
        """, domain['id'], self.params['id'], 'queued'
        await conn.execute(*qu)

    def on_vm_taken(self):
        initial_size = self.params['initial_size']
        if initial_size > len(self.queue._queue):
            self.add_domain()

    def add_domain(self):
        from vdi.tasks import vm
        g.init()
        params = {
            'pool_name': self.params['name'],
            'domain_id': self.params['template_id'],
            'datapool_id': self.params['datapool_id'],
            'controller_ip': self.params['controller_ip'],
            'node_id': self.params['node_id'],
        }
        task = vm.CopyDomain(**params).task
        task.add_done_callback(self.on_vm_created)
        self.pending += 1
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

    @classmethod
    @enter_context(lambda: db.connect())
    async def load_vms(conn, cls, pool):
        vms = await vm.ListVms(controller_ip=pool['controller_ip'])
        valid_ids = {v['id'] for v in vms}
        qu = f"SELECT * FROM vm WHERE pool_id = $1", pool['id']
        vms = await conn.fetch(*qu)
        return [
            dict(v.items()) for v in vms if v['id'] in valid_ids
        ]

    @classmethod
    def get_pool(cls, pool_id):
        if pool_id in cls.instances:
            return cls.instances[pool_id]
        with db.connect() as conn:
            qu = f"SELECT * from pool where id = $1", id
            [params] = await conn.fetch(*qu)
            return cls(params=params)


    @classmethod
    @enter_context(lambda: db.connect())
    async def init(conn, cls, id, block=False):
        """
        Init the pool (possibly, after service restart)
        """
        qu = f"SELECT * from pool where id = $1", id
        [params] = await conn.fetch(*qu)
        ins = cls(params=params)
        Pool.instances[params['id']] = ins
        # locate vms
        qu = f"SELECT * from vm where vm.pool_id = $1", id
        vms = await conn.fetch(*qu)


        add_domains = ins.add_domains()
        if block:
            await add_domains

        return ins


    instances = {}

    # TODO from_db
    # TODO any created vm -> db

# pool = Pool()

