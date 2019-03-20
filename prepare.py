#!/usr/bin/env python
from vdi.tasks import admin
from vdi.settings import settings

import asyncio

async def main():
    if not settings['debug']:
        return
    node = '192.168.20.121'
    await admin.AddNode(management_ip=node)
    print(f'Node {node} is added.')
    await admin.DownloadImage(target='image.qcow2')
    print('.qcow image is downloaded.')
    await admin.UploadImage(filename='image.qcow2')
    print('File upload finished.')


asyncio.run(main())