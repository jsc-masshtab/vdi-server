import os

from sanic import Sanic
from sanic.response import json
from sanic_jwt import exceptions
from sanic_jwt import initialize
from sanic_jwt.decorators import protected

from vdi.settings import settings
from vdi.db import db

if settings['debug']:
    try:
        from aoiklivereload import LiveReloader
        reloader = LiveReloader()
        reloader.start_watcher_thread()
    except:
        pass


def store_refresh_token(*args, **kwargs):
    raise NotImplementedError
    # user_id = kwargs.get("user_id")
    # user = userid_table.get(user_id)
    # refresh_token = kwargs.get("refresh_token")
    # setattr(user, "refresh_token", refresh_token)
    # user.refresh_token = refresh_token
    # save_users()


async def retrieve_user(request, *args, **kwargs):
    user_id_key = 'username' # TODO imports
    if user_id_key in kwargs:
        user_id = kwargs.get(user_id_key)
    else:
        if "payload" in kwargs:
            payload = kwargs.get("payload")
        else:
            payload = request.app.auth.extract_payload(request)
        user_id = payload.get(user_id_key)

    async with db.connect() as conn:
        fields = ['username', 'email']
        qu = f'''SELECT {' ,'.join(fields)} FROM public.user WHERE username = $1''', user_id
        [usr] = await conn.fetch(*qu)
    return dict(usr.items())


def retrieve_refresh_token(request, *args, **kwargs):
    raise NotImplementedError
    # user = request.app.auth.retrieve_user(request, **kwargs)
    # return user.refresh_token

async def authenticate(request, *args, **kwargs):
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username or not password:
        raise exceptions.AuthenticationFailed("Missing username or password.")

    async with db.connect() as conn:
        fields = ['username', 'password', 'email']
        qu = f"SELECT {', '.join(fields)} FROM public.user WHERE username = $1", username
        users = await conn.fetch(*qu)

    if not users:
        raise exceptions.AuthenticationFailed("User not found.")

    [usr] = users

    if password != usr['password']:
        raise exceptions.AuthenticationFailed("Password is incorrect.")

    usr = dict(usr.items())
    return usr


app = Sanic()

app.config.SANIC_JWT_SECRET = "this_is_secret"
app.config.SANIC_JWT_REFRESH_TOKEN_ENABLED = False
app.config.SANIC_JWT_CLAIM_IAT = True
app.config.SANIC_JWT_CLAIM_NBF = True
app.config.SANIC_JWT_USER_ID = "username"
app.config.SANIC_JWT_AUTHORIZATION_HEADER_PREFIX = "jwt"


initialize(
    app,
    authenticate=authenticate,
    # store_refresh_token=store_refresh_token,
    # retrieve_refresh_token=retrieve_refresh_token,
    retrieve_user=retrieve_user,
)


@app.listener('before_server_start')
async def setup_db(app, loop):
    await db.init()


@app.route("/hello")
async def test(request):
    return json({"hello": "world"})


@app.route("/protected")
@protected()
async def protected(request):
    return json({"protected": True})


def entry_point():
    import runpy
    runpy.run_module('sanic', run_name='__main__')