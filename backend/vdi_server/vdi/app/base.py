import sys

from classy_async import g

from starlette.applications import Starlette
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from vdi.app.auth.jwt import JWTAuthenticationBackend
from vdi.db import db
from vdi.settings import settings

app = Starlette(debug=settings.get('debug'))

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


@app.on_event('startup')
async def startup():
    g.use_threadlocal(False)
    await db.init()


app.add_middleware(AuthenticationMiddleware, backend=JWTAuthenticationBackend())
app.add_middleware(SessionMiddleware, secret_key='sphere')

if settings.get('debug'):
    app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'],
                       allow_credentials=True)


