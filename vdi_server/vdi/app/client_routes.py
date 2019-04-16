
import json

from starlette.authentication import requires
from starlette.responses import JSONResponse, PlainTextResponse

from asyncpg.connection import Connection

from vdi.context_utils import enter_context
from vdi.db import db
from vdi.pool import Pool
from vdi.tasks import thin_client


from . import app


@app.route('/client/{pool}', methods=['POST', 'GET'])
# @requires('authenticated')
async def get_vm(request):
    name = request.path_params['pool']
    for pool in Pool.instances.values():
        if pool.params['name'] == name:
            break
    else:
        assert 0
    vm = await pool.queue.get()
    pool.on_vm_taken()
    addr = await thin_client.PrepareVm(domain_id=vm['id'])
    return JSONResponse(addr)


@app.route('/client/login', methods=['POST', 'GET'])
@enter_context(lambda: db.connect())
async def login(conn: Connection, request):
    if request.method == 'GET':
        data = request.query_params
    else:
        data = json.loads(request.data)

    qu = "select password from public.user where username = $1", data['username']
    [[value]] = await conn.fetch(*qu)
    assert value == data['password']
    request.session.update(username=data['username'])
    return PlainTextResponse('ok')


@app.route('/check', methods=['GET', 'POST'])
@requires(['authenticated'])
def check(request):
    username = request.user.username
    return JSONResponse({
        'user': username
    })
