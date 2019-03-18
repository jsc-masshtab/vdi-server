
from vdi.tasks import admin
from vdi.settings import settings

from g_tasks import g

async def run():
    if not settings['debug']:
        return
    await admin.UploadImage(filename='image.qcow2')