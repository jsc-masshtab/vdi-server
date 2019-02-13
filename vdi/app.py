import sys

from starlette.applications import Starlette
from starlette.responses import JSONResponse

from .settings import settings

app = Starlette(**settings)

from g_tasks import g

from .tasks import disk, vm
from .pool import pool


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


@app.route('/vm')
async def get_vm(request):
    vm = await pool.queue.get()
    pool.on_vm_taken()
    return JSONResponse({
        vm['id']: vm
    })

@app.route('/available')
async def pool_state(request):
    vms = {
        vm['id']: vm for vm in pool.queue._queue
    }
    return JSONResponse(vms)


@app.on_event('startup')
async def startup():
    await pool.initial_tasks()

