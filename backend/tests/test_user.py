from vdi.graphql_api import schema
from fixtures.fixtures import (
    fixt_db, conn, fixt_create_static_pool, fixt_entitle_user_to_pool
)

import pytest

@pytest.mark.asyncio
async def test_user_entitlement(fixt_entitle_user_to_pool):

    assert fixt_entitle_user_to_pool['ok']


@pytest.mark.asyncio
async def test_assign_vm_to_user(fixt_entitle_user_to_pool):
    #
    pool_id = fixt_entitle_user_to_pool['pool_id']

    # get pool data
    qu = '''
    query{
      pool(id: %i){
        vms{
          id
        }
      }
    }
    ''' % pool_id
    res = await schema.exec(qu)
    print('t_res_vm', res['pool']['vms'])
    assert len(res['pool']['vms']) == 2

    # assign first vm to user
    vm_id = res['pool']['vms'][0]['id']
    username = 'admin'
    qu = '''
    mutation {
     assignVmToUser(vm_id: "%s", username: "%s") {
       ok
     }
    }
    ''' % (vm_id, username)
    res = await schema.exec(qu)
    #print('test_res', res)
    assert res['assignVmToUser']['ok']

    # remove assignment
    qu = '''
    mutation {
     freeVmFromUser(vm_id: "%s") {
       ok
     }
    }
    ''' % vm_id
    res = await schema.exec(qu)
    assert res['freeVmFromUser']['ok']