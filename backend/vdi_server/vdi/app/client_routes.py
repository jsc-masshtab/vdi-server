
import json

from starlette.authentication import requires
from starlette.responses import JSONResponse, PlainTextResponse


from vdi.pool import Pool
from vdi.tasks import thin_client

from vdi.context_utils import enter_context
from vdi.db import db

from . import app

@app.route('/client/pools')
@requires('authenticated')
async def get_pools(request):
    #FIXME filter by user
    user = request.user.username
    # query = """
    # """
    li = [
        {
            'id': id,
            'name': pool.params['name'],
        }
        for id, pool in Pool.instances.items()
    ]
    return JSONResponse(li)


@app.route('/client/pools/{pool_id}', methods=['GET', 'POST'])
@requires('authenticated')
async def get_vm(request):
    async with db.connect() as conn:
        # FIXME
        controller_ip = '192.168.20.120'

        user = request.user.username
        pool_id = int(request.path_params['pool_id'])
        qu = """
        select id from vm where username = $1 and pool_id = $2
        """, user, pool_id
        vms = await conn.fetch(*qu)
        if vms:
            [(id,)] = vms
            info = await thin_client.GetDomainInfo(controller_ip=controller_ip, domain_id=id)
            return JSONResponse({
                'host': controller_ip,
                'port': info['remote_access_port'],
                'password': info['graphics_password'],
            })
        pool = Pool.instances[pool_id]
        domain = await pool.queue.get()
        qu = "update vm set username = $1 where id = $2", user, domain['id']
        await conn.fetch(*qu)
        pool.on_vm_taken()
        info = await thin_client.PrepareVm(controller_ip=controller_ip, domain_id=domain['id'])
        return JSONResponse({
            'host': controller_ip,
            'port': info['remote_access_port'],
            'password': info['graphics_password'],
        })


@app.route('/check', methods=['GET', 'POST'])
@requires(['authenticated'])
def check(request):
    username = request.user.username
    return JSONResponse({'user': username})
