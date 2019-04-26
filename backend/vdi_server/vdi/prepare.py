#!/usr/bin/env python
from vdi.tasks import admin, resources
from vdi.settings import settings

from classy_async import Wait

import asyncio

from vdi.context_utils import enter_context
from vdi.db import db


async def add_controller(ip):
    await db.init()
    async with db.connect() as conn:
        await conn.fetch("""
            INSERT INTO controller(ip) VALUES ('192.168.20.120')
            ON CONFLICT DO NOTHING
            """)



async def main():
    if not settings['debug']:
        return
    await add_controller('192.168.20.120')
    tasks = [
        admin.AddNode(management_ip='192.168.20.121', controller_ip=settings['controller_ip']),
        admin.DownloadImage(target='image.qcow2'),
    ]
    node_id = None
    async for cls, result in Wait(*tasks).items():
        print(cls.__name__)
        if cls is admin.AddNode:
            node_id = result
    [datapool] = await resources.ListDatapools(controller_ip=settings['controller_ip'], node_id=node_id)
    await admin.UploadImage(filename='image.qcow2', controller_ip=settings['controller_ip'],
                            datapool_id=datapool['id'])
    print('UploadImage')




if __name__ == '__main__':
    asyncio.run(main())