import asyncio
from websockets.exceptions import ConnectionClosed as WsConnectionClosed

from starlette.authentication import requires
from starlette.responses import JSONResponse

from vdi.auth import fetch_token
from db.db import db
from vdi.pool import AutomatedPoolManager
from vdi.tasks import thin_client
from vdi.settings import settings
#from vdi.utils import print

from vdi.errors import NotFound


from .app import app


@app.route('/client/pools')
@requires('authenticated')
async def get_pools(request):

    user = request.user.username

    if user == 'admin':
        async with db.connect() as conn:
            qu = "SELECT * from pool"
            data = await conn.fetch(qu)
    else: # any other user
        async with db.connect() as conn:
            qu = """
            SELECT * from pool JOIN pools_users ON pool.id = pools_users.pool_id
            WHERE pools_users.username = $1
            """, user
            data = await conn.fetch(*qu)

    # list of dictionaries
    pools_data = [
        dict(item)
        for item in data
    ]
    li = [
        {
            'id': pool['id'],
            'name': pool['name'],
        }
        for pool in pools_data
    ]
    return JSONResponse(li)


@app.route('/client/pools/{pool_id}', methods=['GET', 'POST'])
async def get_vm(request):
    from vdi.graphql_api.pool import DesktopPoolType
    user = request.user.username
    pool_id = int(request.path_params['pool_id'])
    # Сочитание pool id и имя пользователя должно быть обязательо уникальным
    # так как пользователь не может иметь больше одной машины в пуле
    async with db.connect() as conn:
        qu = (
            'select controller_ip, desktop_pool_type, vm.id '
            'from pool left join vm on vm.pool_id = pool.id and vm.username = $1 '
            'where pool.id = $2', user, pool_id
        )
        data = await conn.fetch(*qu)
    if not data:
        return JSONResponse({'host': '', 'port': 0, 'password': '',
                             'message': 'Пул не найден'})
    [[controller_ip, desktop_pool_type, vm_id]] = data
    print('data', data)

    if vm_id:
        from vdi.tasks.vm import GetDomainInfo
        info = await GetDomainInfo(controller_ip=controller_ip, domain_id=vm_id)
        await thin_client.PrepareVm(controller_ip=controller_ip, domain_id=vm_id)
        print('remote_access_port', info['remote_access_port'])
        return JSONResponse({
            'host': controller_ip,
            'port': info['remote_access_port'],
            'password': info['graphics_password'],
        })
    # If the user does not have a vm in the pool then try to assign a free vm to him
    # find a free vm in pool
    async with db.connect() as conn:
        qu = "select id from vm where pool_id = $1 and username is NULL limit 1", pool_id
        free_vm = await conn.fetch(*qu)
        print('get_vm: free_vm', free_vm)
        # if there is no free vm then send empty fields??? Handle on thin client side
        if not free_vm:
            return JSONResponse({'host': '', 'port': 0, 'password': '',
                             'message': 'В пуле нет свободных машин'})
        # assign vm to the user
        [(domain_id,)] = free_vm

        qu = "update vm set username = $1 where id = $2", user, domain_id
        await conn.fetch(*qu)

    # post actions for AUTOMATED pool (todo: run in another courutine)
    if desktop_pool_type == DesktopPoolType.AUTOMATED.name:
        pool = AutomatedPoolManager.get_pool(pool_id)
        await pool.on_vm_taken()

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
    print('do_action_on_vm')
    username = request.user.username
    pool_id = int(request.path_params['pool_id'])
    vm_action = request.path_params['action']
    # in pool find machine which belongs to user
    async with db.connect() as conn:
        qu = """                                                                                        
        select id from vm where username = $1 and pool_id = $2                                          
        """, username, pool_id
        vms = await conn.fetch(*qu)

    if vms:
        [(vm_id,)] = vms
    else: # There is no vm with requested pool_id
        return JSONResponse({'error': 'Нет вм с указанным pool_id'})

    # in body info about whether action is forced
    try:
        body = await request.body()
        text_body = body.decode("utf-8")
    except ValueError: # no response body
        text_body = ''
    print('do_action_on_vm: text_body', text_body)

    # determine vm controller ip by pool id
    async with db.connect() as conn:
        qu = """SELECT controller_ip FROM pool WHERE pool.id =  $1""", pool_id
        [(controller_ip,)] = await conn.fetch(*qu)
        print('controller_ip_', controller_ip)
    # do action
    await thin_client.DoActionOnVm(controller_ip=controller_ip, domain_id=vm_id, action=vm_action, body=text_body)

    return JSONResponse({'error': 'null'})


@app.route('/client/auth', methods=['GET', 'POST'])
async def auth(request):
    if request.scope['method'] == 'GET':
        params = request.query_params
    elif request.scope['method'] == 'POST':
        params = await request.json()
    params = {
        'username': params['username'],
        'password': params['password'],
    }
    data = await fetch_token(**params)
    return JSONResponse({'token': data['access_token']})


@app.websocket_route('/ws/client/vdi_server_check')
async def vdi_online_ws_endpoint(websocket):

    WS_TIMEOUT = 1
    await websocket.accept()
    try:
        while True:
            await websocket.send_bytes(b"1")
            await asyncio.sleep(WS_TIMEOUT)
    except WsConnectionClosed:
        pass