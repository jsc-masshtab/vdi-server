#!/usr/bin/env python
from vdi.tasks import admin
from vdi.settings import settings

from vdi.asyncio_utils import Wait

import asyncio

from contextlib import contextmanager, ExitStack
import os
import sys

@contextmanager
def debugger():
    with ExitStack() as stack:
        if os.environ.get('PDB') or os.environ.get('DEBUG'):
            stack.enter_context(drop_into_debugger())
        yield


async def main():
    with debugger():
        if not settings['debug']:
            return
        node = '192.168.20.121'
        tasks = {
            'add_node': admin.AddNode(management_ip=node),
            'download_image': admin.DownloadImage(target='image.qcow2'),
        }
        # async for name, result in Wait(**tasks):
        async for name, _ in Wait(**tasks):
            if name == 'add_node':
                print(f'Node {node} is added.')
            elif name == 'download_image':
                print('.qcow2 image is downloaded.')
        await admin.UploadImage(filename='image.qcow2')
        print('File upload finished.')





class drop_into_debugger:
    def __enter__(self):
        pass
    def __exit__(self, e, m, tb):
        if not e:
            return
        try:
            import ipdb as pdb
        except ImportError:
            import pdb
        print(m.__repr__(), file=sys.stderr)
        pdb.post_mortem(tb)


if __name__ == '__main__':
    asyncio.run(main())