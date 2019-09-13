
import pytest
import json
import uuid
from async_generator import async_generator, yield_, asynccontextmanager

from vdi.tasks.resources import DiscoverControllers
from vdi.tasks import resources
from vdi.tasks import vm

from vdi.graphql_api import schema
from vdi.graphql_api.pool import RemovePool

from vdi.prepare import get_most_appropriate_controller
from vdi import prepare

from db.db import db

@pytest.fixture
async def fixt_db():

    await db.get_pool()
    return db


@pytest.fixture
@async_generator
async def image_name():

    await prepare.main()
    await yield_('image')
    print('image destroy')


@pytest.fixture
@async_generator
async def create_template(fixt_db, image_name):
    qu = '''
    mutation {
      createTemplate(image_name: "%(image_name)s") {
        poolwizard {
          reserve_size
          initial_size
          datapool_id
          node_id
          cluster_id
          controller_ip
          template_id
        }
      }
    }
    ''' % locals()
    r = await schema.exec(qu)
    poolwizard = r['createTemplate']['poolwizard']
    await yield_(poolwizard)
    print('destroy vm')
    qu = '''
    mutation {
      dropTemplate(id: "%(template_id)s") {
        ok
      }
    }
    ''' % poolwizard
    await schema.exec(qu)


@pytest.fixture
@async_generator
async def pool_settings(create_template):
    return {
        'settings': create_template,
    }


@pytest.fixture
@async_generator
def pool_name():
    import random, string
    uid = ''.join(
        random.choice(string.ascii_letters) for _ in range(3)
    )
    return "pool-{}".format(uid)



@pytest.fixture
@async_generator
async def create_pool(create_template, pool_name, pool_settings):
    r = await schema.exec('''
        mutation($settings: PoolSettingsInput) {
          addPool(name: "%(pool_name)s", settings: $settings, block: true) {
            id
          }
        }
        ''' % locals(), pool_settings)
    id = r['addPool']['id']
    await yield_( {
        'id': id,
    } )
    print('destroy pool')
    qu = '''
    mutation {
      removePool(id: %(id)s) {
        ok
      }
    }
    ''' % locals()
    await schema.exec(qu)


@pytest.fixture
@async_generator
async def conn():
    async with db.connect() as c:
        await yield_(c)


@pytest.fixture
@async_generator
async def fixt_create_static_pool(fixt_db):

    print('create_static_pool')
    controller_ip = await get_most_appropriate_controller()
    print('fixt_create_static_pool: controller_ip', controller_ip)

    # choose resources to create vms
    list_of_clusters = await resources.ListClusters(controller_ip=controller_ip)
    print('list_of_clusters', list_of_clusters)

    # find cluster with nodes
    cluster_id = next(cluster['id'] for cluster in list_of_clusters if cluster['nodes_count'] != 0)

    list_of_nodes = await resources.ListNodes(controller_ip=controller_ip, cluster_id=cluster_id)
    print('list_of_nodes', list_of_nodes)
    # find active node
    node_id = next(node['id'] for node in list_of_nodes if node['status'] == 'ACTIVE')

    async def create_domain():
        uid = str(uuid.uuid4())[:7]
        domain_info = await vm.CreateDomain(verbose_name="test_vm_static_pool-{}".format(uid),
                                            controller_ip=controller_ip, node_id=node_id)
        return domain_info

    domain_info_1 = await create_domain()
    domain_info_2 = await create_domain()
    print('domain_info_1 id', domain_info_1['id'])

    # create pool
    vm_ids_list = json.dumps([domain_info_1['id'], domain_info_2['id']])
    qu = '''
        mutation {
          addStaticPool(name: "test_pool_static", vm_ids_list: %s) {
            id
            vms {
              id
            }
          }
        }
        ''' % vm_ids_list

    pool_create_res = await schema.exec(qu)  # ([('addStaticPool', OrderedDict([('id', 88)]))])
    print('pool_create_res', pool_create_res)

    pool_id = pool_create_res['addStaticPool']['id']
    vms = pool_create_res['addStaticPool']['vms']
    await yield_({
        'id': pool_id,
        'vms': vms
    })

    # remove pool
    await RemovePool.do_remove(pool_id)



@pytest.fixture
@async_generator
async def fixt_create_user(fixt_db):

    username = 'test_user_name'
    password = 'test_user_password'
    remove_pool_mutation = '''
    createUser(username: "%s", password: "%s"){
      ok
    }
    ''' % (username, password)
    user_creation_res = await schema.exec(remove_pool_mutation)

    await yield_(username)

    # remove user...


@pytest.fixture
@async_generator
async def fixt_entitle_user_to_pool(fixt_create_static_pool):

    pool_id = fixt_create_static_pool['id']

    # entitle user to pool
    user_name = "admin"
    qu = '''
    mutation {
      entitleUsersToPool(pool_id: %i, entitled_users: ["%s"]) {
        ok
      }
    }
    ''' % (pool_id, user_name)
    res = await schema.exec(qu)
    print('test_res', res)

    await yield_({
        'pool_id': pool_id,
        'ok': res['entitleUsersToPool']['ok']
    })

    # remove entitlement
    qu = '''
    mutation {
    removeUserEntitlementsFromPool(pool_id: %i, entitled_users: ["%s"]
      free_assigned_vms: true
    ) {
      ok
    }
    }
    ''' % (pool_id, user_name)
    res = await schema.exec(qu)
