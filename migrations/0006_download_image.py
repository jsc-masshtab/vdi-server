
from vdi.tasks import admin
from vdi.settings import settings

from g_tasks import g

async def run():
    if not settings['debug']:
        return
    g.init()
    await admin.AddNode()
    await admin.DownloadImage(target='image.qcow2')