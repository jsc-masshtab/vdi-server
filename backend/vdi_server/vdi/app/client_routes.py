
import json

from starlette.authentication import requires
from starlette.responses import JSONResponse, PlainTextResponse


from vdi.pool import Pool
from vdi.tasks import thin_client


from . import app

@app.route('/client/pools')
# @requires('authenticated')
async def get_vm(request):
    #FIXME filter by user
    data = {
        id: pool.params
        for id, pool in Pool.instances.items()
    }
    return JSONResponse(data)


@app.route('/client/{pool_id}', methods=['POST', 'GET'])
# @requires('authenticated')
async def get_vm(request):
    pool_id = int(request.path_params['pool_id'])
    pool = Pool.instances[pool_id]
    # for pool in Pool.instances.values():
    #     if pool.params['name'] == name:
    #         break
    # else:
    #     assert 0
    vm = await pool.queue.get()
    pool.on_vm_taken()
    addr = await thin_client.PrepareVm(domain_id=vm['id'])
    return JSONResponse(addr)


@app.route('/check', methods=['GET', 'POST'])
@requires(['authenticated'])
def check(request):
    username = request.user.username
    return JSONResponse({
        'user': username
    })
