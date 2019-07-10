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
        print('get_pools: data', data)
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


# get vm id from db
# put in another file??
async def get_vm_id_from_db(user, pool_id):
    async with db.connect() as conn:

        qu = """                                                                                        
        select id from vm where username = $1 and pool_id = $2                                          
        """, user, pool_id
        vms = await conn.fetch(*qu)

        if vms:
            [(id,)] = vms
            return id
        else:
            return None

#
async def do_action_on_vm(request, action_str: str):
    pool_id = int(request.path_params['pool_id'])
    id = await get_vm_id_from_db(request.user.username, pool_id)

    if id is not None:
        controller_ip = settings['controller_ip']
        await thin_client.DoActionOnVm(controller_ip=controller_ip, domain_id=id, action=action_str)
        return JSONResponse({'error': 'null'})
    else:
        return JSONResponse({'error': 'There is no vm with requested pool_id'})


@app.route('/client/pools/start/{pool_id}', methods=['GET', 'POST'])
@requires('authenticated')
async def start_vm(request):
    json_response = await do_action_on_vm(request, 'start')
    return json_response


@app.route('/client/pools/suspend/{pool_id}', methods=['GET', 'POST'])
@requires('authenticated')
async def suspend_vm(request):
    json_response = await do_action_on_vm(request, 'suspend')
    return json_response


@app.route('/client/pools/resume/{pool_id}', methods=['GET', 'POST'])
@requires('authenticated')
async def resume_vm(request):
    json_response = await do_action_on_vm(request, 'resume')
    return json_response


@app.route('/client/pools/reset/{pool_id}', methods=['GET', 'POST'])
@requires('authenticated')
async def reset_vm(request):
    json_response = await do_action_on_vm(request, 'reset')
    return json_response


@app.route('/check', methods=['GET', 'POST'])
@requires(['authenticated'])
def check(request):
    username = request.user.username
    return JSONResponse({'user': username})


# qu = "delete from vm where i
#await conn.fetch(*qu)
#return JSONResponse({})
