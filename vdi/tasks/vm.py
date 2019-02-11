from g_tasks import Task

from .base import CONTROLLER_URL, Token
from . import disk

# POST http://192.168.20.120/api/domains/
#
# cpu_count: 1
# cpu_priority: "10"
# memory_count: 1024
# node: "882950b8-0ef9-40ef-ad46-4ab109112462"
# os_type: "Other"
# sound: {model: "ich6", codec: "micro"}
# verbose_name: "kvi"
# video: {type: "cirrus", vram: "16384", heads: "1"}


class GetNode(Task):

    1


class CreateDomain(Task):

    url = f'{CONTROLLER_URL}/api/domains/'