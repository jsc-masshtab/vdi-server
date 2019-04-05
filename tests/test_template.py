import pytest

from vdi.tasks.vm import SetupDomain
from vdi.tasks import admin

from vdi.asyncio_utils import Wait

from vdi.graphql.schema import exec

@pytest.fixture
async def image_name():
    node = '192.168.20.121'
    add_node = admin.AddNode(management_ip=node)
    image_name = 'image.qcow2'
    download_image = admin.DownloadImage(target=image_name)
    async for result, type in Wait(add_node, download_image).items():
        if type is admin.AddNode:
            print(f'Node {node} is added.')
        elif type is admin.DownloadImage:
            print('.qcow image is downloaded.')
    await admin.UploadImage(filename=image_name)
    print('File upload finished.')
    return image_name


# @pytest.fixture
# async def template_vm(image_name):
#     r = await SetupDomain(image_name=image_name)
#     return r

@pytest.mark.asyncio
async def test_create_template(image_name):
    qu = f'''
    mutation {{
      createTemplate(image_name: "{image_name}") {{
        template {{
            id
        }}
      }}
    }}
    '''
    r = await exec(qu)
    assert r.data

@pytest.mark.asyncio
async def test_drop_template(template_id):
    1

#TODO teardown fixture