
from vdi.tasks import admin
from vdi.settings import settings

from g_tasks import g

async def run():
    if not settings['debug']:
        return
    await admin.AddNode(management_ip='192.168.20.121')
    await admin.DownloadImage(target='image.qcow2')