import json
import attr

import asyncio
from .asyncio_utils import callback

from g_tasks import g

from dataclasses import dataclass

from cached_property import cached_property as cached

@dataclass()
class Pool:
    template_id: str
    name: str = None
    pending: int = 0


    @cached
    def queue(self):
        return asyncio.Queue()

    @cached
    def tasks(self):
        'TODO'

    @callback
    async def on_vm_created(self, fut):
        if fut.exception():
            # FIXME
            print(fut.exception())
            return
        domain = fut.result()
        await self.queue.put(domain)
        self.queue.task_done()
        self.pending -= 1

    def on_vm_taken(self):
        self.add_domain()

    def add_domain(self):
        from vdi.tasks import vm
        g.init()
        task = vm.CopyDomain(domain_id=self.template_id).ensure_task()
        task.add_done_callback(self.on_vm_created)
        self.pending += 1
        return task

    async def schedule_tasks(self):
        conf = self.get_config()
        initial_size = conf['initial_size']

        domains = []

        for i in range(initial_size):
            d = await self.add_domain()
            domains.append(d)

        return domains


    @classmethod
    def get_config(cls):
        # FIXME remove
        conf = {
            'vm_type': 'disco',
            'vm_name_prefix': 'ubuntu',
            'initial_size': 2,
            'reserve_size': 2,
        }
        return conf

    instances = {}


# pool = Pool()

