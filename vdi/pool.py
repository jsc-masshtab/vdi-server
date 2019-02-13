import json
import attr

import asyncio
from .asyncio_utils import callback

from g_tasks import g

@attr.s(auto_attribs=True)
class Pool:
    queue: asyncio.Queue = asyncio.Queue()

    @callback
    async def on_vm_created(self, fut):
        if fut.exception():
            # FIXME
            print(fut.exception())
            return
        domain = fut.result()
        await self.queue.put(domain)
        self.queue.task_done()

    def on_vm_taken(self):
        self.add_domain()

    def add_domain(self):
        from vdi.tasks import vm
        g.init()
        task = vm.SetupDomain().ensure_task()
        task.add_done_callback(self.on_vm_created)

    async def initial_tasks(self):
        conf = self.get_config()
        initial_size = conf['initial_size']

        for i in range(initial_size):
            self.add_domain()

    def get_config(self):
        conf = {
            'vm_type': 'disco',
            'vm_name_prefix': 'ubuntu',
            'initial_size': 2,
            'reserve_size': 2,
        }
        return conf


pool = Pool()

