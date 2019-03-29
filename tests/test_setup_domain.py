import pytest

from vdi.tasks.vm import SetupDomain
from vdi.tasks import admin

from vdi.asyncio_utils import Wait

from vdi.graphql.schema import exec

@pytest.fixture
async def image_name():
    node = '192.168.20.121'
    add_node = admin.AddNode(management_ip=node).ensure_task()
    image_name = 'image.qcow2'
    download_image = admin.DownloadImage(target=image_name).ensure_task()
    async for result, task in Wait(add_node, download_image).items():
        if task.type is admin.AddNode:
            print(f'Node {node} is added.')
        elif task.type is admin.DownloadImage:
            print('.qcow image is downloaded.')
    await admin.UploadImage(filename=image_name)
    print('File upload finished.')
    return image_name


# @pytest.fixture
# async def template_vm(image_name):
#     r = await SetupDomain(image_name=image_name)
#     return r

@pytest.mark.asyncio
async def test(image_name):
    qu = f'''
    mutation {{
      createTemplate(image_name: {image_name}) {{
        id
      }}
    }}
    '''
    r = await exec(qu)
    print(r.data)


#TODO teardown fixture