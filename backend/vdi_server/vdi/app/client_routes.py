from starlette.authentication import requires
from starlette.responses import JSONResponse
from vdi.db import db
from vdi.pool import Pool
from vdi.tasks import thin_client
from vdi.settings import settings

from . import app

@app.route('/client/pools')
@requires('authenticated')
async def get_pools(request):
    #FIXME filter by user
    # user = request.user.username
    async with db.connect() as conn:
        qu = f"SELECT * from pool"
        data = await conn.fetch(qu)
    pools = [
        Pool(params=dict(item))
        for item in data
    ]
    li = [
        {
            'id': pool.params['id'],
            'name': pool.params['name'],
        }
        for pool in pools
    ]
    return JSONResponse(li)


@app.route('/client/pools/{pool_id}', methods=['GET', 'POST'])
@requires('authenticated')
async def get_vm(request):
    async with db.connect() as conn:
        # FIXME
        controller_ip = settings['controller_ip']
        user = request.user.username
        pool_id = int(request.path_params['pool_id'])
        qu = """
        select id from vm where username = $1 and pool_id = $2
        """, user, pool_id
        vms = await conn.fetch(*qu)
        if vms:
            [(id,)] = vms
            from vdi.tasks.vm import GetDomainInfo
            info = await GetDomainInfo(controller_ip=controller_ip, domain_id=id)
            return JSONResponse({
                'host': controller_ip,
                'port': info['remote_access_port'],
                'password': info['graphics_password'],
            })

        # try to wake pool if it's empty
        if pool_id not in Pool.instances:
            await Pool.wake_pool(pool_id)
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
