import json
import uuid

import asyncio
from .asyncio_utils import callback

from g_tasks import g

from dataclasses import dataclass

from cached_property import cached_property as cached

from vdi.db import db
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
    @db.connect()
    async def on_vm_created(self, fut, conn: Connection):
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

    def generate_name(self):
        uid = uuid.uuid4()
        return f"{self.params['name']}-{uid}"

    def add_domain(self):
        from vdi.tasks import vm
        g.init()
        template_id = self.params['template_id']
        vm_name = self.generate_name()
        task = vm.CopyDomain(domain_id=template_id, vm_name=vm_name).task
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


    instances = {}

    # TODO from_db
    # TODO any created vm -> db

# pool = Pool()

