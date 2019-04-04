#!/usr/bin/env python
from vdi.tasks import admin
from vdi.settings import settings

from vdi.asyncio_utils import Wait

import asyncio


async def main():
    if not settings['debug']:
        return
    node = '192.168.20.121'
    tasks = [
        admin.AddNode(management_ip=node),
        admin.DownloadImage(target='image.qcow2'),
    ]
    async for cls, _ in Wait(*tasks).items():
        if cls is admin.AddNode:
            print(f'Node {node} is added.')
        elif cls is admin.DownloadImage:
            print('.qcow2 image is downloaded.')
    await admin.UploadImage(filename='image.qcow2')
    print('File upload finished.')




if __name__ == '__main__':
    asyncio.run(main())