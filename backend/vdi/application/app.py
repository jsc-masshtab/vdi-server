import sys

#from classy_async.classy_async import g

from starlette.applications import Starlette
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from vdi.auth.jwt import JWTAuthenticationBackend
from db.db import db
from vdi.settings import settings

app = Starlette(debug=settings.get('debug'))

from vdi.auth import VDIUser
from vdi.application import Request

from ..pool import PoolObject, AutomatedPoolManager


@app.middleware("http")
async def init_context(request, call_next):
    #g.init()
    await Request.set(request)
    user = request.user
    if not isinstance(user, VDIUser):
        user = None
    await VDIUser.set(user)
    response = await call_next(request)
    return response


# @app.middleware("http")
# async def debug(request, call_next):
#     try:
#         return await call_next(request)
#     except:
#         if settings.get('debug'):
#             e, m, tb = sys.exc_info()
#             print(m.__repr__(), file=sys.stderr)
#             from ipdb import post_mortem
#             post_mortem(tb)
#         raise


@app.on_event('startup')
async def startup():
    await db.get_pool()

    # init pools live data
    async with db.connect() as conn:
        qu = "SELECT * from pool WHERE deleted IS NOT true"
        pools_data = await conn.fetch(qu)
        for pool_data in pools_data:
            pool_data_dict = dict(pool_data.items())
            pool_object = PoolObject(params=pool_data_dict)
            AutomatedPoolManager.pool_instances[pool_data_dict['id']] = pool_object
    # Check pools health and update statuses


app.add_middleware(AuthenticationMiddleware, backend=JWTAuthenticationBackend())
app.add_middleware(SessionMiddleware, secret_key='sphere')

if settings.get('is_dev'):
    app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'],
                       allow_credentials=True)

from . import client_routes, admin_routes