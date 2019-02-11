import sys

from starlette.applications import Starlette
from starlette.responses import JSONResponse

from .settings import settings

app = Starlette(**settings)

from g_tasks import g

from . import tasks

# import typing
#
# class VmInfo(typing.NamedTuple):
#     type: str
#     name: str

@app.middleware("http")
async def add_custom_header(request, call_next):
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
    await tasks.ImportDisk()
    r = {
        'name': request.query_params['vm_name']
    }
    return JSONResponse(r)

