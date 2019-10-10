from vdi.graphql_api import schema
from fixtures.fixtures import (
    fixt_db, conn, fixt_create_static_pool, fixt_entitle_user_to_pool, fixt_create_user
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


@pytest.mark.asyncio
async def test_change_password(fixt_create_user):

    username = fixt_create_user['username']
    old_password = fixt_create_user['password']
    new_password = 'test_user_password2'
    # change password
    qu = '''
    mutation {
      changePassword(username: "%s", password: "%s", new_password: "%s"){
        ok
      }
    }
    ''' % (username, old_password, new_password)
    res = await schema.exec(qu)
    assert res['changePassword']['ok']

    # set password back
    qu = '''
    mutation {
      changePassword(username: "%s", password: "%s", new_password: "%s"){
        ok
      }
    }
    ''' % (username, new_password, old_password)
    res = await schema.exec(qu)
    assert res['changePassword']['ok']
