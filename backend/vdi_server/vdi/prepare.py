#!/usr/bin/env python
import json
from vdi.tasks import admin, resources
from vdi.settings import settings

from classy_async import Wait
from vdi.tasks import Token

import asyncio

from vdi.db import db

class FirstTimeToken(Token):
    creds = {
        'username': 'admin',
        'password': 'veil',
    }


async def add_controller(ip):
    from vdi.graphql.resources import AddController
    await db.init()
    await AddController._add_controller(ip=ip, set_default=True)

async def add_user(controller_ip, **creds):
    url = f"http://{controller_ip}/api/users/"

    token = await FirstTimeToken(controller_ip=controller_ip)
    headers = {
        "Content-Type": 'application/json',
        'Authorization': f'jwt {token}',
    }
    body = dict(creds or settings.credentials)
    body.update({
        'groups': ['Administrator', 'Storage Administrator', 'Security Administrator',
                   'VM Administrator', 'VM Operator',]
    })
    body = json.dumps(body)
    from vdi.tasks.client import HttpClient, FetchException
    client = HttpClient()
    try:
        await client.fetch(url, method='POST', body=body, headers=headers)
    except FetchException as ex:
        if 'Пользователь с таким именем уже существует.' not in str(ex):
            raise


async def main():
    if not settings['is_dev']:
        return
    controller_ip = settings['controller_ip']

    await add_user(controller_ip)
    await add_controller(controller_ip)
    # tasks = [
    #     admin.AddNode(management_ip='192.168.20.121', controller_ip=settings['controller_ip']),
    #     admin.DownloadImage(target='image.qcow2'),
    # ]
    # node_id = None
    # async for cls, result in Wait(*tasks).items():
    #     print(f"{cls.__name__} done")
    #     if cls is admin.AddNode:
    #         node_id = result
    # [datapool] = await resources.ListDatapools(controller_ip=settings['controller_ip'], node_id=node_id)
    # await admin.UploadImage(filename='image.qcow2', controller_ip=settings['controller_ip'],
    #                         datapool_id=datapool['id'])
    # print('UploadImage done')




if __name__ == '__main__':
    asyncio.run(main())