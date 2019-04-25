#!/usr/bin/env python
from vdi.tasks import admin
from vdi.settings import settings

from classy_async import Wait

import asyncio


async def add_controller():
    'TODO'

async def main():
    if not settings['debug']:
        return
    params = await admin.discover_resources()
    tasks = [
        admin.AddNode(management_ip=params['node']['management_ip'], controller_ip=params['controller_ip']),
        admin.DownloadImage(target='image.qcow2'),
    ]
    async for cls, _ in Wait(*tasks).items():
        if cls is admin.AddNode:
            print(f'Node is added.')
        elif cls is admin.DownloadImage:
            print('.qcow2 image is downloaded.')
    await admin.UploadImage(filename='image.qcow2', controller_ip=params['controller_ip'],
                            datapool_id=params['datapool']['id'])
    print('File upload finished.')




if __name__ == '__main__':
    asyncio.run(main())