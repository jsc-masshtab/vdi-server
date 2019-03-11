import sys

from starlette.applications import Starlette
from starlette.responses import JSONResponse

from .settings import settings

from . import app

from g_tasks import g

from .tasks import disk, vm
from .pool import Pool
from .db import db


@app.middleware("http")
async def init_g_context(request, call_next):
    g.init()
    g.set_attr('request', request)
    response = await call_next(request)
    return response


@app.middleware("http")
async def debug(request, call_next):
    try:
        return await call_next(request)
    except:
        if settings.get('debug'):
            e, m, tb = sys.exc_info()
            print(m.__repr__(), file=sys.stderr)
            from ipdb import post_mortem
            post_mortem(tb)
        raise


def get_pool():
    for _, p in Pool.instances.items():
        if p.params['name'] and 'pub' in p.params['name']:
            return p
    assert 0

@app.route('/client', methods=['POST', 'GET'])
async def get_vm(request):
    breakpoint()
    pool = get_pool()
    vm = await pool.queue.get()
    pool.on_vm_taken()
    return JSONResponse({
        vm['id']: vm
    })


@app.route('/client/login', methods=['POST', 'GET'])
async def login(request):
    1


@app.on_event('startup')
async def startup():
    await db.init()


import vdi.graphql.pool
