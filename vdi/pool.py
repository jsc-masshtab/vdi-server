import json
import attr
import uuid

import asyncio
from tornado.httpclient import AsyncHTTPClient

from . import settings

from . import tasks

'''
TODO
'''

@attr.s(auto_attribs=True)
class Pool(dict):
    pending: set = set()
    queue: asyncio.Queue = asyncio.Queue()

    @classmethod
    def get_pool(cls, vm_config):
        return cls.instance  # a stub

    def get_info(self):
        return {
            'pending': list(self.pending),
            'available': list(self.queue._queue),
        }

    @property
    def min_size(self):
        return settings.pool_size

    max_size = min_size

    def has_reserve(self):
        '''
        Pool has extra vms for some reason.
        Prevents the creation of a new vm after taking one from queue.
        '''
        return False

    def initial_tasks(self):
        for i in range(self.min_size):
            yield self.create_vm()

    async def create_vm(self):
        id = str(uuid.uuid1()).split('-')[0]
        name = f'vdi_{id}'
        http_client = AsyncHTTPClient()
        # FIXME use a func. call
        url = f'http://localhost:8003/create_disk?vm_name={name}&vm_type=fedora'
        self.pending.add(id)
        await http_client.fetch(url, **tasks.TIMEOUT)
        await self.queue.put(name)
        self.queue.task_done()
        self.pending.discard(id)


# TODO cli tio remove disks


pool = Pool()

