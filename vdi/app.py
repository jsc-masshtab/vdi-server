import sys

from starlette.applications import Starlette
from starlette.responses import JSONResponse

from .settings import settings

app = Starlette(**settings)

from g_tasks import g

from .tasks import disk, vm
from .pool import pool

# import typing
#
# class VmInfo(typing.NamedTuple):
#     type: str
#     name: str

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
async def homepage(request):
    domain = await vm.SetupDomain()
    r = {
        'name': request.query_params['vm_name'],
        'id': domain['id'],
    }
    return JSONResponse(r)


@app.on_event('startup')
def startup():
    # only schedule
    # TODO
    pool.initial_tasks()

