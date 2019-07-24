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

    user = request.user.username

    async with db.connect() as conn:
        qu = f"""
        SELECT * from pool JOIN pools_users ON pool.id = pools_users.pool_id
        WHERE pools_users.username = $1
        """, user
        data = await conn.fetch(*qu)
    print('data', data)
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

            await thin_client.PrepareVm(controller_ip=controller_ip, domain_id=id)
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

    print('get_vm_id_from_db: vms', vms)
    if vms:
        [(id,)] = vms
        return id
    else:
        return None


@app.route('/client/pools/{pool_id}/{action}', methods=['POST'])
@requires('authenticated')
async def do_action_on_vm(request):

    username = request.user.username
    pool_id = int(request.path_params['pool_id'])
    vm_action = request.path_params['action']

    id = await get_vm_id_from_db(username, pool_id)
    
    if id is None:
        return JSONResponse({'error': 'There is no vm with requested pool_id'})

    # in body info about whether action is forced
    try:
        body = await request.body()
        text_body = body.decode("utf-8")
    except ValueError: # no response body
        text_body = ''
    print('do_action_on_vm: text_body', text_body)

    # do action
    controller_ip = settings['controller_ip']
    await thin_client.DoActionOnVm(controller_ip=controller_ip, domain_id=id, action=vm_action, body=text_body)

    return JSONResponse({'error': 'null'})


@app.route('/check', methods=['GET', 'POST'])
@requires(['authenticated'])
def check(request):
    username = request.user.username
    return JSONResponse({'user': username})

