from starlette.authentication import requires
from starlette.responses import JSONResponse
from vdi.db import db
from vdi.pool import Pool
from vdi.tasks import thin_client
from vdi.settings import settings
from vdi.errors import SimpleError
from ..graphql.pool import DesktopPoolType


from . import app


@app.route('/client/pools')
@requires('authenticated')
async def get_pools(request):
    user = request.user.username

    if user == 'admin':
        async with db.connect() as conn:
            qu = f"SELECT * from pool"
            data = await conn.fetch(qu)
    else: # any other user
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
        print('controller_ip', controller_ip)
        # determine desktop pool type
        qu = 'select desktop_pool_type from pool where id = $1', pool_id
        pools = await conn.fetch(*qu)
        [(desktop_pool_type,)] = pools
        print('get_vm: desktop_pool_type', desktop_pool_type)

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

        # AUTOMATED
        if desktop_pool_type == DesktopPoolType.AUTOMATED.name:
            # try to wake pool if it's empty
            if pool_id not in Pool.instances:
                await Pool.wake_pool(pool_id)
            pool = Pool.instances[pool_id]
            domain = await pool.queue.get()
            domain_id = domain['id']
            qu = "update vm set username = $1 where id = $2", user, domain_id
            await conn.fetch(*qu)
            await pool.on_vm_taken()
        # STATIC
        elif desktop_pool_type == DesktopPoolType.STATIC.name:
            # find a free vm in static pool
            qu = f"select id from vm where pool_id = $1 and username is NULL limit 1", pool_id
            free_vms = await conn.fetch(*qu)
            print('get_vm: free_vm', free_vms)
            # if there is no free vm then send empty fields??? Handle on thin client side
            if not free_vms:
                return JSONResponse({'host': '', 'port': 0, 'password': '',
                                     'message': 'В статическом пуле нет свободных машин'})
            # assign vm to the user
            [(domain_id,)] = free_vms
            qu = f"update vm set username = $1 where id = $2", user, domain_id
            await conn.fetch(*qu)
        else:
            raise RuntimeError("Wrong desktop pool type")
        # send data to thin client
        info = await thin_client.PrepareVm(controller_ip=controller_ip, domain_id=domain_id)
        return JSONResponse({
            'host': controller_ip,
            'port': info['remote_access_port'],
            'password': info['graphics_password'],
        })


@app.route('/client/pools/{pool_id}/{action}', methods=['POST'])
@requires('authenticated')
async def do_action_on_vm(request):

    username = request.user.username
    pool_id = int(request.path_params['pool_id'])
    vm_action = request.path_params['action']

    async with db.connect() as conn:
        qu = """                                                                                        
        select id from vm where username = $1 and pool_id = $2                                          
        """, username, pool_id
        vms = await conn.fetch(*qu)

    print('do_action_on_vm: vms', vms)
    if vms:
        [(vm_id,)] = vms
    else:
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
    await thin_client.DoActionOnVm(controller_ip=controller_ip, domain_id=vm_id, action=vm_action, body=text_body)

    return JSONResponse({'error': 'null'})


@app.route('/check', methods=['GET', 'POST'])
@requires(['authenticated'])
def check(request):
    username = request.user.username
    return JSONResponse({'user': username})

