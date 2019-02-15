'''
Usage:
    run <path.to.Command>
'''

import asyncio
from pprint import pprint
from docopt import docopt

from vdi.import_utils import import_obj


def run_cmd(cmd):
    try:
        *_, cls = import_obj(cmd)
    except ImportError:
        *_, cls = import_obj(f'vdi.tasks.{cmd}')
    asyncio.run(_run_task(cls))

async def _run_task(cls):
    result = await cls().fresh_context()
    pprint(result)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    cmd = arguments['<path.to.Command>']
    run_cmd(cmd)